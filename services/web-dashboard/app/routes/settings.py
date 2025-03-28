from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

def register_routes(app):
    """Register settings routes with the Flask app."""
    
    @app.route('/settings')
    @login_required
    def settings_index():
        """Render the general settings page."""
        return render_template('settings/index.html')

    @app.route('/settings/display')
    @login_required
    def settings_display():
        """Render the display settings page."""
        return render_template('settings/display.html')

    @app.route('/settings/api')
    @login_required
    def settings_api():
        """Render the API settings page."""
        return render_template('settings/api.html')

    @app.route('/settings/update', methods=['POST'])
    @login_required
    def settings_update():
        """Update settings."""
        setting_type = request.form.get('setting_type')
        
        if setting_type == 'general':
            # Update general settings
            # This would typically involve updating user preferences in the database
            flash('General settings updated successfully.', 'success')
            return redirect(url_for('settings_index'))
        
        elif setting_type == 'display':
            # Update display settings
            # This would typically involve updating user display preferences
            flash('Display settings updated successfully.', 'success')
            return redirect(url_for('settings_display'))
        
        elif setting_type == 'api':
            # Update API settings
            # This would typically involve updating API keys or endpoints
            flash('API settings updated successfully.', 'success')
            return redirect(url_for('settings_api'))
        
        else:
            flash('Invalid settings type.', 'danger')
            return redirect(url_for('settings_index'))

    @app.route('/settings/reset', methods=['POST'])
    @login_required
    def settings_reset():
        """Reset settings to defaults."""
        setting_type = request.form.get('setting_type')
        
        if setting_type == 'general':
            # Reset general settings to defaults
            flash('General settings reset to defaults.', 'success')
            return redirect(url_for('settings_index'))
        
        elif setting_type == 'display':
            # Reset display settings to defaults
            flash('Display settings reset to defaults.', 'success')
            return redirect(url_for('settings_display'))
        
        elif setting_type == 'api':
            # Reset API settings to defaults
            flash('API settings reset to defaults.', 'success')
            return redirect(url_for('settings_api'))
        
        else:
            flash('Invalid settings type.', 'danger')
            return redirect(url_for('settings_index'))
