from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flasgger import Swagger
import json
import os
import base64
import uuid
import re

app = Flask(__name__)
DATA_FILE = 'data/database/data.json'
UPLOAD_FOLDER = 'data/uploads'

# Swagger Configuration
app.config['SWAGGER'] = {
    'title': 'NewTab Dashboard API',
    'uiversion': 3
}
swagger_config = Swagger.DEFAULT_CONFIG.copy()
swagger_config['specs_route'] = '/swagger/'
swagger = Swagger(app, config=swagger_config)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/database', exist_ok=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"pages": [{"id": "default", "name": "Home"}], "systems": [], "presets": []}
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Migration: old format (list) -> new format (dict)
            if isinstance(data, list):
                return {"pages": [{"id": "default", "name": "Home"}], "systems": data, "presets": []}
            # Ensure presets key exists
            if 'presets' not in data:
                data['presets'] = []
            return data
    except:
        return {"pages": [{"id": "default", "name": "Home"}], "systems": [], "presets": []}

PRESETS_FILE = 'config/presets.json'

def load_presets():
    """Load presets from presets.json file"""
    if not os.path.exists(PRESETS_FILE):
        return []
    try:
        with open(PRESETS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

@app.route('/')
def index():
    """
    Main dashboard page
    ---
    parameters:
      - name: page
        in: query
        type: string
        required: false
        default: default
        description: The ID of the page to display
    responses:
      200:
        description: Success
    """
    data = load_data()
    page_id = request.args.get('page', 'default')
    pages = data.get('pages', [])
    systems = data.get('systems', [])
    settings = data.get('settings', {})
    if 'search_enabled' not in settings: settings['search_enabled'] = True
    if 'search_base_url' not in settings: 
        settings['search_base_url'] = "https://www.google.com/search?q="
    if 'search_placeholder' not in settings:
        settings['search_placeholder'] = "Google Search"
    if 'search_width' not in settings:
        settings['search_width'] = "300"
    if 'ticker_symbols' not in settings:
        settings['ticker_symbols'] = "AAPL, MSFT, TSLA, SPY, QQQ"
    if 'ticker_enabled' not in settings:
        settings['ticker_enabled'] = False
    if 'footer_enabled' not in settings:
        settings['footer_enabled'] = True

    
    # Filter systems by page, keeping original indices
    filtered = []
    for i, s in enumerate(systems):
        if page_id in s.get('pages', ['default']):
            s_copy = dict(s)
            s_copy['_index'] = i
            filtered.append(s_copy)
    
    current_page = next((p for p in pages if p['id'] == page_id), {'id': 'default', 'name': 'Home'})
    
    return render_template('index.html', systems=filtered, pages=pages, current_page=current_page, settings=settings)

@app.route('/admin')
def admin():
    """
    Admin configuration page
    ---
    responses:
      200:
        description: Success
    """
    data = load_data()
    settings = data.get('settings', {})
    if 'search_enabled' not in settings: settings['search_enabled'] = True
    if 'search_base_url' not in settings: 
        settings['search_base_url'] = "https://www.google.com/search?q="
    if 'search_placeholder' not in settings:
        settings['search_placeholder'] = "Google Search"
    if 'search_width' not in settings:
        settings['search_width'] = "300"
    if 'ticker_symbols' not in settings:
        settings['ticker_symbols'] = "AAPL, MSFT, TSLA, SPY, QQQ"
    if 'ticker_enabled' not in settings:
        settings['ticker_enabled'] = False
    if 'footer_enabled' not in settings:
        settings['footer_enabled'] = True

    presets = sorted(load_presets(), key=lambda x: x['name'].lower())
    return render_template('admin.html', pages=data.get('pages', []), systems=data.get('systems', []), settings=settings, presets=presets)

@app.route('/admin/settings', methods=['POST'])
def update_settings():
    """
    Update global dashboard settings
    ---
    parameters:
      - name: search_enabled
        in: formData
        type: string
        enum: [on, off]
      - name: search_base_url
        in: formData
        type: string
      - name: search_placeholder
        in: formData
        type: string
      - name: search_width
        in: formData
        type: integer
      - name: footer_text
        in: formData
        type: string
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    current_settings = data.get('settings', {})
    search_enabled = request.form.get('search_enabled') == 'on'
    search_base_url = request.form.get('search_base_url', '').strip()
    search_placeholder = request.form.get('search_placeholder', '').strip()
    search_width = request.form.get('search_width', '').strip()
    footer_text = request.form.get('footer_text', current_settings.get('footer_text', 'Made with Love by DevOps Team'))
    footer_enabled = request.form.get('footer_enabled') == 'on'
    cards_per_row = request.form.get('cards_per_row', current_settings.get('cards_per_row', '0'))
    ticker_enabled = request.form.get('ticker_enabled') == 'on'
    ticker_symbols = request.form.get('ticker_symbols', 'AAPL, MSFT, TSLA, SPY, QQQ')
    try:
        cards_per_row = int(cards_per_row)
        if cards_per_row < 0 or cards_per_row > 10:
            cards_per_row = 0
    except (ValueError, TypeError):
        cards_per_row = 0
    data['settings'] = {
        'search_enabled': search_enabled,
        'search_base_url': search_base_url,
        'search_placeholder': search_placeholder,
        'search_width': search_width,
        'footer_enabled': footer_enabled,
        'footer_text': footer_text,
        'cards_per_row': cards_per_row,
        'ticker_enabled': ticker_enabled,
        'ticker_symbols': ticker_symbols,
        'default_card_style': current_settings.get('default_card_style', {})
    }
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/bulk_style', methods=['POST'])
def bulk_style():
    """ Apply styling either to global defaults or to all current cards """
    data = load_data()
    action = request.form.get('bulk_action', 'defaults')
    
    style = {
        'tag_bg_color': request.form.get('tag_bg_color'),
        'tag_opacity': int(request.form.get('tag_opacity', '80')),
        'tag_position': request.form.get('tag_position'),
        'title_bg_enabled': request.form.get('title_bg_enabled') == 'on',
        'title_bg_color': request.form.get('title_bg_color'),
        'title_bg_opacity': int(request.form.get('title_bg_opacity', '80')),
        'title_text_light': request.form.get('title_text_light'),
        'title_text_dark': request.form.get('title_text_dark'),
        'back_color': request.form.get('back_color'),
        'image_mode': request.form.get('image_mode'),
        'front_color': request.form.get('front_color'),
        'image_size': request.form.get('image_size', '80'),
    }
    
    if action == 'defaults':
        if 'settings' not in data:
            data['settings'] = {}
        data['settings']['default_card_style'] = style
    elif action == 'all':
        for system in data.get('systems', []):
            system.update({k: v for k,v in style.items() if v is not None})
            
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/api/reorder', methods=['POST'])
def reorder():
    """
    Reorder elements using their original indices.
    """
    try:
        req_data = request.get_json()
        new_order = req_data.get('order', [])
        
        data = load_data()
        systems = data.get('systems', [])
        
        if new_order:
            target_indices = sorted(new_order)
            systems_copy = list(systems)
            
            for target_idx, orig_idx in zip(target_indices, new_order):
                systems[target_idx] = systems_copy[int(orig_idx)]
                
            save_data(data)
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ========== PAGE MANAGEMENT ==========
@app.route('/admin/pages/add', methods=['POST'])
def add_page():
    """
    Add a new dashboard page
    ---
    parameters:
      - name: page_name
        in: formData
        type: string
        required: true
        description: The display name of the page
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    name = request.form.get('page_name', '').strip()
    if name:
        page_id = slugify(name)
        # Avoid duplicates
        if not any(p['id'] == page_id for p in data['pages']):
            data['pages'].append({'id': page_id, 'name': name})
            save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/pages/delete/<page_id>', methods=['POST'])
def delete_page(page_id):
    """
    Delete a dashboard page
    ---
    parameters:
      - name: page_id
        in: path
        type: string
        required: true
        description: The ID of the page to delete
    responses:
      302:
        description: Redirects back to admin page
    """
    if page_id == 'default':
        return redirect(url_for('admin'))  # Cannot delete default
    data = load_data()
    data['pages'] = [p for p in data['pages'] if p['id'] != page_id]
    # Remove page from all systems
    for system in data['systems']:
        if page_id in system.get('pages', []):
            system['pages'].remove(page_id)
    save_data(data)
    return redirect(url_for('admin'))

# ========== SYSTEM MANAGEMENT ==========
@app.route('/admin/add', methods=['POST'])
def add_system():
    """
    Add a new system (card) to the dashboard
    ---
    parameters:
      - name: name
        in: formData
        type: string
        required: true
      - name: back_color
        in: formData
        type: string
      - name: front_color
        in: formData
        type: string
      - name: image_mode
        in: formData
        type: string
        enum: [fit, fill]
      - name: image_size
        in: formData
        type: integer
      - name: preset_image
        in: formData
        type: string
      - name: link_text[]
        in: formData
        type: array
        items: {type: string}
      - name: link_url[]
        in: formData
        type: array
        items: {type: string}
      - name: assigned_pages[]
        in: formData
        type: array
        items: {type: string}
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    
    name = request.form.get('name', 'New Card')
    tag_input = request.form.get('tag', '')
    tags = [t.strip() for t in tag_input.split(',') if t.strip()]
    back_color = request.form.get('back_color', '#000000')
    image_mode = request.form.get('image_mode', 'fill')
    front_color = request.form.get('front_color', '#11161F')
    image_size = request.form.get('image_size', '80')
    tag_bg_color = request.form.get('tag_bg_color', '#0f172a')
    tag_opacity = request.form.get('tag_opacity', '80')
    tag_position = request.form.get('tag_position', 'top-right')
    
    title_bg_enabled = request.form.get('title_bg_enabled') == 'on'
    title_bg_color = request.form.get('title_bg_color', '#ffffff')
    title_bg_opacity = request.form.get('title_bg_opacity', '80')
    title_text_light = request.form.get('title_text_light', '#1e293b')
    title_text_dark = request.form.get('title_text_dark', '#e2e8f0')
    link_texts = request.form.getlist('link_text[]')
    link_urls = request.form.getlist('link_url[]')
    assigned_pages = request.form.getlist('assigned_pages[]')
    
    if not assigned_pages:
        assigned_pages = ['default']
    
    links = [{'text': t, 'url': u} for t, u in zip(link_texts, link_urls) if t and u]
    
    image_filename = 'generic.png'
    
    file = request.files.get('image_file')
    if file and file.filename:
        filename = f"{uuid.uuid4()}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        image_filename = filename
    
    pasted_data = request.form.get('pasted_image')
    if pasted_data and 'base64,' in pasted_data:
        header, encoded = pasted_data.split(',', 1)
        ext = 'png'
        if 'image/jpeg' in header: ext = 'jpg'
        
        decoded = base64.b64decode(encoded)
        filename = f"{uuid.uuid4()}.{ext}"
        with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
            f.write(decoded)
        image_filename = filename
    
    # Check for preset image (built-in images in static/presets/)
    preset_image = request.form.get('preset_image')
    if preset_image and image_filename == 'generic.png':
        image_filename = preset_image

    data['systems'].append({
        'name': name,
        'tags': tags,
        'tag_bg_color': tag_bg_color,
        'tag_opacity': int(tag_opacity) if tag_opacity.isdigit() else 80,
        'tag_position': tag_position,
        'title_bg_enabled': title_bg_enabled,
        'title_bg_color': title_bg_color,
        'title_bg_opacity': int(title_bg_opacity) if title_bg_opacity.isdigit() else 80,
        'title_text_light': title_text_light,
        'title_text_dark': title_text_dark,
        'image': image_filename,
        'image_mode': image_mode,
        'image_size': image_size,
        'back_color': back_color,
        'front_color': front_color,
        'links': links,
        'pages': assigned_pages
    })
    
    save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/update/<int:id>', methods=['POST'])
def update_system(id):
    """
    Update an existing system (card)
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The index of the system to update
      - name: name
        in: formData
        type: string
        required: true
      - name: back_color
        in: formData
        type: string
      - name: front_color
        in: formData
        type: string
      - name: image_mode
        in: formData
        type: string
        enum: [fit, fill]
      - name: image_size
        in: formData
        type: integer
      - name: link_text[]
        in: formData
        type: array
        items: {type: string}
      - name: link_url[]
        in: formData
        type: array
        items: {type: string}
      - name: assigned_pages[]
        in: formData
        type: array
        items: {type: string}
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    systems = data.get('systems', [])
    
    if 0 <= id < len(systems):
        name = request.form.get('name')
        tag_input = request.form.get('tag', '')
        tags = [t.strip() for t in tag_input.split(',') if t.strip()]
        back_color = request.form.get('back_color', '#000000')
        image_mode = request.form.get('image_mode', 'fill')
        front_color = request.form.get('front_color', '#11161F')
        image_size = request.form.get('image_size', '80')
        tag_bg_color = request.form.get('tag_bg_color', '#0f172a')
        tag_opacity = request.form.get('tag_opacity', '80')
        tag_position = request.form.get('tag_position', 'top-right')
        
        title_bg_enabled = request.form.get('title_bg_enabled') == 'on'
        title_bg_color = request.form.get('title_bg_color', '#ffffff')
        title_bg_opacity = request.form.get('title_bg_opacity', '80')
        title_text_light = request.form.get('title_text_light', '#1e293b')
        title_text_dark = request.form.get('title_text_dark', '#e2e8f0')
        link_texts = request.form.getlist('link_text[]')
        link_urls = request.form.getlist('link_url[]')
        assigned_pages = request.form.getlist('assigned_pages[]')
        
        if not assigned_pages:
            assigned_pages = ['default']
        
        links = [{'text': t, 'url': u} for t, u in zip(link_texts, link_urls) if t and u]
        
        current_image = systems[id].get('image', 'generic.png')
        image_filename = current_image
        
        # Check for preset image first (so it can be overridden by upload if both present, though UI prevents this)
        preset_image = request.form.get('preset_image')
        if preset_image:
            image_filename = preset_image
        
        file = request.files.get('image_file')
        if file and file.filename:
            filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_filename = filename
        
        pasted_data = request.form.get('pasted_image')
        if pasted_data and 'base64,' in pasted_data:
            header, encoded = pasted_data.split(',', 1)
            ext = 'png'
            if 'image/jpeg' in header: ext = 'jpg'
            
            decoded = base64.b64decode(encoded)
            filename = f"{uuid.uuid4()}.{ext}"
            with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
                f.write(decoded)
            image_filename = filename

        system_data = {
            'name': name,
            'tags': tags,
            'tag_bg_color': tag_bg_color,
            'tag_opacity': int(tag_opacity) if tag_opacity.isdigit() else 80,
            'tag_position': tag_position,
            'title_bg_enabled': title_bg_enabled,
            'title_bg_color': title_bg_color,
            'title_bg_opacity': int(title_bg_opacity) if title_bg_opacity.isdigit() else 80,
            'title_text_light': title_text_light,
            'title_text_dark': title_text_dark,
            'image': image_filename,
            'image_mode': image_mode,
            'image_size': image_size,
            'back_color': back_color,
            'front_color': front_color,
            'links': links,
            'pages': assigned_pages
        }
        systems[id] = system_data
        
        save_data(data)
        
        return_url = request.form.get('return_url')
        if return_url:
            separator = '&' if '?' in return_url else '?'
            return redirect(f"{return_url}{separator}edit=1")
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_system(id):
    """
    Delete a system (card) from the dashboard
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: The index of the system to delete
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    systems = data.get('systems', [])
    if 0 <= id < len(systems):
        systems.pop(id)
        save_data(data)
    return redirect(url_for('admin'))

@app.route('/admin/move/<direction>/<int:id>', methods=['POST'])
def move_system(direction, id):
    """
    Move a system card up or down in the list
    ---
    parameters:
      - name: direction
        in: path
        type: string
        enum: [up, down]
        required: true
      - name: id
        in: path
        type: integer
        required: true
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    systems = data.get('systems', [])
    
    if direction == 'up' and id > 0 and id < len(systems):
        systems[id], systems[id-1] = systems[id-1], systems[id]
        save_data(data)
    elif direction == 'down' and id < len(systems) - 1 and id >= 0:
        systems[id], systems[id+1] = systems[id+1], systems[id]
        save_data(data)
        
    return redirect(url_for('admin'))

@app.route('/admin/move-to/<int:from_index>/<int:to_index>', methods=['POST'])
def move_system_to(from_index, to_index):
    data = load_data()
    systems = data.get('systems', [])
    
    if 0 <= from_index < len(systems) and 0 <= to_index < len(systems):
        item = systems.pop(from_index)
        systems.insert(to_index, item)
        save_data(data)
            
    return redirect(url_for('admin'))

@app.route('/api/reorder', methods=['POST'])
def api_reorder():
    """
    Reorder systems via JSON API (used by homepage drag-and-drop)
    ---
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            order:
              type: array
              items: {type: integer}
    responses:
      200:
        description: Success
    """
    from flask import jsonify
    data = load_data()
    systems = data.get('systems', [])
    order = request.get_json(force=True).get('order', [])
    
    if len(order) == len(systems) and sorted(order) == list(range(len(systems))):
        data['systems'] = [systems[i] for i in order]
        save_data(data)
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Invalid order'}), 400
@app.route('/admin/pages/move/<direction>/<page_id>', methods=['POST'])
def move_page_route(direction, page_id):
    data = load_data()
    pages = data.get('pages', [])
    
    # Find index of page with page_id
    index = next((i for i, p in enumerate(pages) if p['id'] == page_id), -1)
    
    if index != -1:
        if direction == 'up' and index > 0:
            pages[index], pages[index-1] = pages[index-1], pages[index]
            save_data(data)
        elif direction == 'down' and index < len(pages) - 1:
            pages[index], pages[index+1] = pages[index+1], pages[index]
            save_data(data)
            
    return redirect(url_for('admin'))

@app.route('/admin/duplicate/<int:id>', methods=['POST'])
def duplicate_system(id):
    """
    Duplicate a system card
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      302:
        description: Redirects back to admin page
    """
    data = load_data()
    systems = data.get('systems', [])
    if 0 <= id < len(systems):
        import copy
        new_system = copy.deepcopy(systems[id])
        new_system['name'] += ' (Copy)'
        systems.insert(id + 1, new_system)
        save_data(data)
    return redirect(url_for('admin'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """
    Serve an uploaded image file
    ---
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: The filename to serve
    responses:
      200:
        description: The image file
      404:
        description: File not found
    """
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8585))
    app.run(debug=True, host='0.0.0.0', port=port)
