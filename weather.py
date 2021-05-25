from flask import Flask, flash, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import requests

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///weather.db',
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return f"[{self.id}] {self.name}"


db.create_all()

api_key = '77444ad2ac8cca93916cdf2c4adfbf53'


def api_call(city):
    """Sends request to openweathermap API for weather data of <city>."""
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    return requests.get(url)


@app.route('/')
def index():
    weathers = []
    cities = City.query.all()
    for city in cities:
        r = api_call(city.name)
        if r:
            response = json.loads(r.text)
            city_name = response['name']
            state = response['weather'][0]['main']
            temp = round(response['main']['temp'])
            # openweathermap API returns city's current time as offset in seconds from UTC
            utc_offset = int(response['timezone'])
            time = datetime.utcnow() + timedelta(seconds=utc_offset)
            hour = int(time.strftime('%H'))
            # convert hour to corresponding CSS class name for card
            if hour < 6 or hour > 20:
                time = "night"
            elif 18 <= hour <= 20 or 6 <= hour <= 8:
                time = "evening-morning"
            else:
                time = "day"
            weather_dict = {'id': city.id, 'city': city_name, 'state': state, 'temp': temp, 'time': time}
            weathers.append(weather_dict)

    return render_template('index.html', weathers=weathers)


@app.route('/add', methods=['GET', 'POST'])
def add_city():
    if request.method == 'POST':
        new_city = City(name=request.form['city_name'].title())
        if api_call(new_city.name):
            db.session.add(new_city)
            try:
                db.session.commit()
            except Exception:
                flash("The city has already been added to the list!")
                db.session.rollback()
        else:
            flash("The city doesn't exist!")

    return redirect('/')


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete_city(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    app.run()
