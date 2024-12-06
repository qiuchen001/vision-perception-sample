from flask import Blueprint, render_template
from ..utils.logger import logger

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

@bp.route('/about')
def about():
    logger.info("Rendering about page")
    return render_template('about.html')