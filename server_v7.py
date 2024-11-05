from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import os
import random

app = Flask(__name__)
socketio = SocketIO(app)

clients = {}

@socketio.on('connect')
def handle_connect():
  client_id = random.randint(1000, 9999)
  clients[client_id] = {'x': 50, 'y': 50}
  emit('new_client', {'id': client_id, 'x': 50, 'y': 50}, broadcast=True)

@socketio.on('move')
def handle_move(data):
  client_id = data['id']
  if client_id in clients:
    clients[client_id]['x'] = data['x']
    clients[client_id]['y'] = data['y']
    emit('update_position', {'id': client_id, 'x': data['x'], 'y': data['y']}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
  client_id = request.sid
  for client_id in list(clients.keys()):
    if client_id not in clients:
      del clients[client_id]


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

comments = []

@app.route('/comments', methods=['GET'])
def get_comments():
    return jsonify({'comments': comments})

@app.route('/')
def index():
    return render_template('index.html', comments=comments)

@app.route('/files', methods=['GET'])
def list_files():
  try:
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({'files': files})
  except Exception as e:
    return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return redirect(url_for('index'))

@socketio.on('new_comment')
def handle_new_comment(comment):
    if comment:
        comments.append(comment)
        emit('update_comments', comments, broadcast=True)

@app.route('/comment', methods=['POST'])
def add_comment():
    comment = request.form['comment']
    if comment:
        comments.append(comment)
        socketio.emit('update_comments', comments)  # Emit the new comment
    return redirect(url_for('index'))

@app.route('/load_file/<filename>', methods=['GET'])
def load_file(filename):
  try:
    with open(os.path.join(UPLOAD_FOLDER, filename), 'r') as file:
      content = file.read()
    return jsonify({'content': content})
  except FileNotFoundError:
    return jsonify({'error': 'File not found'}), 404


@socketio.on('edit_file')
def handle_edit_file(data):
  emit('update_file_content', data, broadcast=True)


@app.route('/save_file', methods=['POST'])
def save_file():
  data = request.form
  content = data.get('content')
  filename = data.get('filename')
  if filename:
    with open(os.path.join(UPLOAD_FOLDER, filename), 'w') as file:
      file.write(content)
  return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
