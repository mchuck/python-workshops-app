""" Main application file """

import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, make_response, jsonify
from src.callbacks import generate_image, create_callback, delete_callback, get_callback_info, rename_callback, process_call


app = Flask(__name__, template_folder='templates')


@app.before_first_request
def load_config():
    load_dotenv()
    conn_string = 'DefaultEndpointsProtocol=https;AccountName={};AccountKey={}'.format(
        os.environ.get('STORAGE_NAME'), os.environ.get('STORAGE_KEY')
    )
    os.environ['CONNECTION_STRING'] = conn_string


@app.route('/', methods=['GET'])
def main_page():
    return render_template('main.html')


@app.route('/', methods=['POST'])
def new_callback():
    if request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
        display_name = request.form['display_name']
        guid = create_callback(display_name)
        return redirect('/%s/' % guid)

    elif request.headers['Content-Type'] == 'application/json':
        display_name = request.json['display_name']
        guid = create_callback(display_name)
        response = {
            'id': guid,
            'display_name': display_name
        }
        return jsonify(response), 201
    
    return '', 415


@app.route('/<guid>/', methods=['GET'])
def get_stats(guid):
    callback_info = get_callback_info(guid)
    return render_template('callback.html',
        callback_name=callback_info['display_name'],
        callback_id=guid)


@app.route('/<guid>/call', methods=['GET'])
def activate_callback(guid):
    log_id = process_call(guid, request.args.get('status', '(unknown)'))
    return jsonify({ 'logId': log_id }), 200


@app.route('/<guid>/', methods=['POST'])
def manage_callback(guid):
    if request.headers['Content-Type'] != 'application/x-www-form-urlencoded':
        return '', 415

    if 'delete' in request.form.keys():
        delete_callback(guid)
        return redirect('/')
    else:
        new_name = request.form['new_name']
        rename_callback(guid, new_name)
        return render_template('callback.html', callback_name=new_name, callback_id=guid)


@app.route('/<guid>/', methods=['PUT'])
def manage_callback_put(guid):
    new_name = request.json['new_name']
    rename_callback(guid, new_name)
    response = {
        'id': guid,
        'display_name': new_name
    }
    return jsonify(response), 200


@app.route('/<guid>/', methods=['DELETE'])
def manage_callback_delete(guid):
    delete_callback(guid)
    return '', 204


@app.route('/<guid>/img', methods=['GET'])
def get_image(guid):
    img_response = make_response(generate_image(guid))
    img_response.headers['Content-Type'] = 'image/png'
    return img_response


@app.route('/favicon.ico/')
def get_favicon():
    return '', 404


if __name__ == '__main__':
    app.run(debug=True)