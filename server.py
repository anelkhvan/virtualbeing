from logger import logger
import traceback
logger.info("Configuration loaded")

# Set up flask
import os
from flask import Flask, request
from flask_cors import cross_origin
from flask import jsonify
from flask import send_file

# from render_local_computer import process
# from render_cloud_server import process
from versionb import process


# Create app
print("Creating flask app...")
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/render', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@cross_origin(origins="*", allow_headers=['Content-Type'], methods=["GET"])
def route_test():
    try:
        text = request.args.get('text')
        logger.info("################ \n ################Text to render: {} \n #################".format(text))

        video_path = process(text)

        return send_file(video_path, as_attachment=True)
    
    except Exception as err:
        tb = traceback.format_exc()
        logger.error('{} {} {} 500 Error\nIP:{}\n{}'.format(request.method, request.scheme, request.full_path, request.headers.get("X-Forwarded-For", request.remote_addr), tb))
        return jsonify({"error": err})


@app.errorhandler(400)
def server_error(e):
    logger.error('{} {} {} 500 Error\nIP:{}\n{}'.format(request.method, request.scheme, request.full_path, request.headers.get("X-Forwarded-For", request.remote_addr), e))
    return jsonify({"error": e})


if __name__ == "__main__":
    import os
    app.run(debug=True, host='0.0.0.0', port=5000)
    # http://localhost:5000?text=I am doing good, how are you? All well with your family?
    # generate_audio("I am doing good, how are you? All well with your family?")
