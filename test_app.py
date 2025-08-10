from app import app

with app.app_context():
    try:
        from flask import render_template_string
        result = render_template_string('Hello {{ name }}', name='World')
        print('Template test OK:', result)
    except Exception as e:
        print('Template test ERROR:', e) 