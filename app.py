from flask import Flask, render_template, request, jsonify, redirect, url_for
from PIL import Image
import os
from io import BytesIO
import google.generativeai as genai
from werkzeug.utils import secure_filename
import markdown

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/describe', methods=['POST'])
def describe():
    additional_context = request.form.get('context', '')
    screenshots = request.files.getlist('screenshots')

    descriptions = []
    saved_image_paths = []

    for screenshot in screenshots:
        filename = secure_filename(screenshot.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot.save(image_path)
        saved_image_paths.append(image_path)

        image = Image.open(image_path)

        context = f"""
        Analyze the provided screenshot to generate a testing guide for the visible features of the digital product.

        ### Expected Output:
        - **Description**: Describe what this test case is about.
        - **Pre-conditions**: What needs to be set up or ensured before testing.
        - **Testing Steps**: Clear, step-by-step instructions on how to perform the test.
        - **Expected Result**: Describe what should happen if the feature works correctly.

        ### Additional Context: {additional_context}
        """
        prompt = [context, image]

        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            response = model.generate_content(prompt)

            html_description = markdown.markdown(response.text)
            descriptions.append(html_description)
        except Exception as e:
            return jsonify({'error': f'Failed to process the screenshot: {str(e)}'}), 500

    results = list(zip(descriptions, saved_image_paths))

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
