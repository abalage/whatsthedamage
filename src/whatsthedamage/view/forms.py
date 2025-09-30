from flask_wtf import FlaskForm
from wtforms import FileField, DateField, StringField, BooleanField
from wtforms.validators import DataRequired, Optional


class UploadForm(FlaskForm):
    filename = FileField(validators=[DataRequired()])
    config = FileField(validators=[Optional()])
    start_date = DateField(format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField(format='%Y-%m-%d', validators=[Optional()])
    filter = StringField()
    verbose = BooleanField()
    no_currency_format = BooleanField()
    ml = BooleanField(default=True)
