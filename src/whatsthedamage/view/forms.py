from flask_wtf import FlaskForm
from wtforms import FileField, DateField, StringField, BooleanField
from wtforms.validators import DataRequired, Optional


class UploadForm(FlaskForm):  # type: ignore
    filename = FileField('CSV file:', render_kw={
        'class': 'form-control',
        'aria-describedby': 'fileHelp'
    }, validators=[DataRequired()])
    config = FileField('Config file:', render_kw={
        'class': 'form-control',
        'aria-describedby': 'configHelp'
    }, validators=[Optional()])
    start_date = DateField('Start Date:', format='%Y-%m-%d', render_kw={
        'class': 'form-control',
        'id': 'start_date',
        'aria-describedby': 'dateStartHelp'
    }, validators=[Optional()])
    end_date = DateField('End Date:', format='%Y-%m-%d', render_kw={
        'class': 'form-control',
        'id': 'end_date',
        'aria-describedby': 'dateEndHelp'
    }, validators=[Optional()])
    filter = StringField('Filter:', render_kw={
        'class': 'form-control',
        'aria-describedby': 'filterHelp'
    })
    verbose = BooleanField('Verbose logs', render_kw={
        'class': 'form-check-input',
        'aria-describedby': 'verboseHelp'
    })
    no_currency_format = BooleanField('No Currency Format', render_kw={
        'class': 'form-check-input',
        'aria-describedby': 'currencyHelp'
    })
