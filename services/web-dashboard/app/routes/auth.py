from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from uuid import UUID
from app import db, login_manager
from app.models import User

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the user ID stored in the session.
    
    Args:
        user_id: The ID of the user to load
        
    Returns:
        The User object or None if not found
    """
    try:
        # Convert string ID to UUID
        uuid_obj = UUID(user_id)
        return User.query.get(uuid_obj)
    except (ValueError, TypeError):
        return None

def register_routes(app):
    """Register authentication routes with the Flask app."""
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle user login.
        
        Returns:
            Rendered login form or redirects to dashboard
        """
        # If user is already logged in, redirect to dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = 'remember' in request.form
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            
            # Validate credentials
            if user and user.check_password(password):
                # Log in the user
                login_user(user, remember=remember)
                
                # Redirect to the page the user was trying to access
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard')
                
                flash('Login successful!', 'success')
                return redirect(next_page)
            else:
                flash('Invalid email or password', 'danger')
        
        return render_template('auth/login.html', title='Login')

    @app.route('/logout')
    def logout():
        """
        Handle user logout.
        
        Returns:
            Redirects to login page
        """
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """
        Handle user registration.
        
        Returns:
            Rendered registration form or redirects to login page
        """
        # If user is already logged in, redirect to dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            username = request.form.get('username')
            name = request.form.get('name')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate form data
            if not email or not username or not name or not password or not confirm_password:
                flash('All fields are required', 'danger')
            elif password != confirm_password:
                flash('Passwords do not match', 'danger')
            elif User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
            elif User.query.filter_by(username=username).first():
                flash('Username already taken', 'danger')
            else:
                # Create new user
                user = User(
                    email=email,
                    username=username,
                    name=name,
                    password=password,
                    role='USER',
                    status='ACTIVE'
                )
                
                # Save to database
                db.session.add(user)
                db.session.commit()
                
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
        
        return render_template('auth/register.html', title='Register')

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """
        Display and update the user's profile.
        
        Returns:
            Rendered profile page template or redirects to profile page after update
        """
        if request.method == 'POST':
            name = request.form.get('name')
            
            # Validate form data
            if not name:
                flash('Name is required', 'danger')
            else:
                # Update user profile
                current_user.name = name
                db.session.commit()
                
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('profile'))
        
        return render_template(
            'auth/profile.html',
            title='My Profile'
        )

    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """
        Handle password change.
        
        Returns:
            Rendered change password form or redirects to profile page
        """
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate form data
            if not current_password or not new_password or not confirm_password:
                flash('All fields are required', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            elif not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
            else:
                # Update password
                current_user.set_password(new_password)
                db.session.commit()
                
                flash('Password changed successfully!', 'success')
                return redirect(url_for('profile'))
        
        return render_template(
            'auth/change_password.html',
            title='Change Password'
        )
