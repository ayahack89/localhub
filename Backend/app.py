from flask import Flask, render_template, abort, send_file, request  # type: ignore
import mimetypes
import os

app = Flask(__name__, template_folder="../Frontend/Templates")

# Index route
@app.route("/")
def home():
    f_path = "./Repositories/"
    try:
        files_and_dir = os.listdir(f_path)
    except FileNotFoundError:
        abort(404)

    files_and_dir.sort()
    files_and_dir = [os.path.join(f_path, item) for item in files_and_dir]

    return render_template("index.html", files_and_dir=files_and_dir, title="Welcome to Local Hub!! : )")

# Repo & file view route
@app.route("/Repositories/<path:repo_path>")
def repo_view(repo_path):
    base_path = "./Repositories/"
    full_path = os.path.join(base_path, repo_path)

    if not os.path.exists(full_path):
        abort(404)

    if os.path.isdir(full_path):
        files_and_dir = os.listdir(full_path)
        files_and_dir.sort()
        files_and_dir = [os.path.join(repo_path, item) for item in files_and_dir]
        return render_template("repo_view.html", files_and_dir=files_and_dir, repo_name=repo_path)

    if os.path.isfile(full_path):
        mime_type, _ = mimetypes.guess_type(full_path)

        # Medias
        if mime_type and mime_type.startswith(('image', 'video', 'audio')):
            return send_file(full_path, mimetype=mime_type)

        # PDF & DOC 
        elif mime_type and mime_type.startswith('application') and (
            full_path.endswith(('.pdf', '.doc', '.docx'))
        ):
            return send_file(full_path, as_attachment=True)

        # (.txt, .md, .html)
        elif mime_type and mime_type.startswith('text'):
            try:
                with open(full_path, 'r', encoding="utf-8") as files:
                    file_read = files.read()
            except UnicodeDecodeError:
                with open(full_path, 'r', encoding="ISO-8859-1") as files:
                    file_read = files.read()

            file_read = file_read.replace('\r\n', '\n').replace('\t', '    ')
            return render_template("file_view.html", content=file_read, file_name=repo_path)

        # Unknown file types 
        else:
            return send_file(full_path, as_attachment=True)

    # Default error
    abort(404)

if __name__ == "__main__":
    app.run(debug=True)
