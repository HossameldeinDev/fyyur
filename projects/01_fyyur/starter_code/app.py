#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
import os
from flask_wtf.csrf import CSRFProtect
from models import db, Venues, Shows, Artists, Genres
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
csrf = CSRFProtect(app)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues =Venues.query.all()
  data = {}
  for venue in venues:
    num_upcoming_shows = 0
    for show in venue.shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    venue_data = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows
    }
    if venue.city in data.keys():
      data[venue.city]["venues"].append(venue_data)
    else:
      data[venue.city] = {
        "city": venue.city,
        "state": venue.state,
        "venues": [venue_data]
      }
  data = list(data.values())
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venues.query.filter(Venues.name.ilike(f'%{search_term}%')).all()
  venues_data = []
  for venue in venues:
    num_upcoming_shows = 0
    for show in venue.shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    venues_data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows,
    })
  response = {
    "count": len(venues),
    "data": venues_data
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venues.query.filter_by(id=venue_id).first()
  data = {}
  if venue:
      id = venue.id
      name = venue.name
      genres = []
      for genre in venue.genres:
          genres.append(genre.name)
      address = venue.address
      city = venue.city
      state = venue.state
      phone = venue.phone
      website = venue.website
      facebook_link = venue.facebook_link
      seeking_talent = venue.seeking_talent
      seeking_description = venue.seeking_description
      image_link = venue.image_link
      artists_with_past_shows = db.session.query(Artists, Shows).join(Shows, Shows.artist_id == Artists.id).\
          join(Venues, Shows.venue_id == venue.id).filter(Shows.start_time <= datetime.now()).all()
      past_shows_count = len(artists_with_past_shows)
      past_shows = []
      for artist, show in artists_with_past_shows:
          past_shows.append( {
              "artist_id": artist.id,
              "artist_name": artist.name,
              "artist_image_link": artist.image_link,
              "start_time": str(show.start_time)
          })
      artists_with_upcoming_shows = db.session.query(Artists, Shows).join(Shows, Shows.artist_id == Artists.id).\
          join(Venues, Shows.venue_id == venue.id).filter(Shows.start_time > datetime.now()).all()
      upcoming_shows_count = len(artists_with_upcoming_shows)
      upcoming_shows = []
      for artist, show in artists_with_upcoming_shows:
          upcoming_shows.append( {
              "artist_id": artist.id,
              "artist_name": artist.name,
              "artist_image_link": artist.image_link,
              "start_time": str(show.start_time)
          })
      data = {
          "id": id,
          "name": name,
          "genres": genres,
          "address":address,
          "city":city,
          "state":state,
          "phone":phone,
          "website":website,
          "facebook_link":facebook_link,
          "seeking_talent":seeking_talent,
          "seeking_description": seeking_description,
          "image_link":image_link,
          "past_shows":past_shows,
          "upcoming_shows":upcoming_shows,
          "past_shows_count":past_shows_count,
          "upcoming_shows_count":upcoming_shows_count
      }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venue_data = VenueForm(request.form)
  if not venue_data.validate():
      flash('An error occurred. Input data is invalid and a new venue could not be listed')
      return render_template('pages/home.html')
  name = venue_data.name.data
  city = venue_data.city.data
  state = venue_data.state.data
  address = venue_data.address.data
  phone = venue_data.phone.data
  facebook_link  = venue_data.facebook_link.data
  image_link  = venue_data.image_link.data
  website_link  = venue_data.website_link.data
  seeking_talent = venue_data.seeking_talent.data
  seeking_description = venue_data.seeking_description.data
  venue_object = Venues(
    name=name,
    address=address,
    city=city,
    state=state,
    phone=phone,
    website=website_link,
    facebook_link=facebook_link,
    seeking_talent=seeking_talent,
    seeking_description=seeking_description,
    image_link=image_link,
  )
  genres = venue_data.genres.data
  for genre in genres:
    genre_object = Genres.query.filter_by(name=genre).first()
    if genre_object:
      venue_object.genres.append(genre_object)
    else:
      venue_object.genres.append(Genres(name=genre))
  try:
    # on successful db insert, flash success
    db.session.add(venue_object)
    db.session.commit()
    flash('Venue ' + name + ' was successfully listed!')
  except:
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venues.query.filter_by(id=venue_id).first()
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully removed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be removed.')
  finally:
    return {'status': 'Success'}

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artists.query.all()
  for artist in artists:
      data.append(
          {
              "id": artist.id,
              "name": artist.name,
          }
      )
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artists.query.filter(Artists.name.ilike(f'%{search_term}%')).all()
  artists_data = []
  for artist in artists:
    num_upcoming_shows = 0
    for show in artist.shows:
      if show.start_time > datetime.now():
        num_upcoming_shows += 1
    artists_data.append(
        {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows,
        }
    )

  response={
    "count": len(artists),
    "data": artists_data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artists.query.filter_by(id=artist_id).first()
  data = {}
  if artist:
      id = artist.id
      name = artist.name
      genres = []
      for genre in artist.genres:
          genres.append(genre.name)
      city = artist.city
      state = artist.state
      phone = artist.phone
      website = artist.website
      facebook_link = artist.facebook_link
      seeking_venue = artist.seeking_venue
      seeking_description = artist.seeking_description
      image_link = artist.image_link
      venues_with_past_shows = db.session.query(Venues, Shows).join(Shows, Shows.venue_id == Venues.id). \
          join(Artists, Shows.artist_id == artist.id).filter(Shows.start_time <= datetime.now()).all()
      past_shows_count = len(venues_with_past_shows)
      past_shows = []
      for venue, show in venues_with_past_shows:
          past_shows.append({
              "venue_id": venue.id,
              "venue_name": venue.name,
              "venue_image_link": venue.image_link,
              "start_time": str(show.start_time)
          })
      venues_with_upcoming_shows = db.session.query(Venues, Shows).join(Shows, Shows.venue_id == Venues.id). \
          join(Artists, Shows.artist_id == artist.id).filter(Shows.start_time > datetime.now()).all()
      upcoming_shows_count = len(venues_with_upcoming_shows)
      upcoming_shows = []
      for venue, show in venues_with_upcoming_shows:
          upcoming_shows.append({
              "venue_id": venue.id,
              "venue_name": venue.name,
              "venue_image_link": venue.image_link,
              "start_time": str(show.start_time)
          })
      data = {
          "id": id,
          "name": name,
          "genres": genres,
          "city":city,
          "state":state,
          "phone":phone,
          "website":website,
          "facebook_link":facebook_link,
          "seeking_venue":seeking_venue,
          "seeking_description": seeking_description,
          "image_link":image_link,
          "past_shows":past_shows,
          "upcoming_shows":upcoming_shows,
          "past_shows_count":past_shows_count,
          "upcoming_shows_count":upcoming_shows_count
      }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_object = Artists.query.filter_by(id=artist_id).first()
  form.name.data = artist_object.name
  form.city.data = artist_object.city
  form.state.data = artist_object.state
  form.phone.data = artist_object.phone
  form.image_link.data = artist_object.image_link
  form.genres.data = artist_object.genres
  form.facebook_link.data = artist_object.facebook_link
  form.website_link.data = artist_object.website
  form.seeking_venue.data = artist_object.seeking_venue
  form.seeking_description.data = artist_object.seeking_description
  artist={
    "id": artist_object.id,
    "name": artist_object.name,
    "genres": artist_object.genres,
    "city": artist_object.city,
    "state": artist_object.state,
    "phone": artist_object.phone,
    "website": artist_object.website,
    "facebook_link": artist_object.facebook_link,
    "seeking_venue": artist_object.seeking_venue,
    "seeking_description": artist_object.seeking_description,
    "image_link": artist_object.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist_data = ArtistForm(request.form)
  if not artist_data.validate():
      flash('An error occurred. Input data is invalid and Artist could not be edited')
      return render_template('pages/home.html')
  artist = Artists.query.filter_by(id=artist_id).first()
  artist.name = artist_data.name.data
  artist.city = artist_data.city.data
  artist.state = artist_data.state.data
  artist.phone = artist_data.phone.data
  artist.image_link = artist_data.image_link.data
  genres = artist_data.genres.data
  artist.genres = []
  for genre in genres:
    genre_object = Genres.query.filter_by(name=genre).first()
    if genre_object:
      artist.genres.append(genre_object)
    else:
      artist.genres.append(Genres(name=genre))
  artist.facebook_link = artist_data.facebook_link.data
  artist.website = artist_data.website_link.data
  artist.seeking_venue = artist_data.seeking_venue.data
  artist.seeking_description = artist_data.seeking_description.data
  try:
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + artist.name + ' was successfully edited!')
  except:
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be edited.')
  finally:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_object = Venues.query.filter_by(id=venue_id).first()
  form.name.data = venue_object.name
  form.genres.data = venue_object.genres
  form.address.data = venue_object.address
  form.city.data = venue_object.city
  form.state.data = venue_object.state
  form.phone.data = venue_object.phone
  form.image_link.data = venue_object.image_link
  form.facebook_link.data = venue_object.facebook_link
  form.website_link.data = venue_object.website
  form.seeking_talent.data = venue_object.seeking_talent
  form.seeking_description.data = venue_object.seeking_description
  venue={
    "id": venue_object.id,
    "name": venue_object.name,
    "genres": venue_object.genres,
    "address": venue_object.address,
    "city": venue_object.city,
    "state": venue_object.state,
    "phone": venue_object.phone,
    "website": venue_object.website,
    "facebook_link": venue_object.facebook_link,
    "seeking_talent": venue_object.seeking_talent,
    "seeking_description": venue_object.seeking_description,
    "image_link": venue_object.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue_data = VenueForm(request.form)
  if not venue_data.validate():
      flash('An error occurred. Input data is invalid and venue could not be edited')
      return render_template('pages/home.html')
  venue = Venues.query.filter_by(id=venue_id).first()
  venue.name = venue_data.name.data
  venue.address = venue_data.address.data
  venue.city = venue_data.city.data
  venue.state = venue_data.state.data
  venue.phone = venue_data.phone.data
  venue.image_link = venue_data.image_link.data
  genres = venue_data.genres.data
  venue.genres = []
  for genre in genres:
    genre_object = Genres.query.filter_by(name=genre).first()
    if genre_object:
      venue.genres.append(genre_object)
    else:
      venue.genres.append(Genres(name=genre))
  venue.facebook_link = venue_data.facebook_link.data
  venue.website = venue_data.website_link.data
  venue.seeking_talent = venue_data.seeking_talent.data
  venue.seeking_description = venue_data.seeking_description.data
  try:
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + venue.name + ' was successfully edited!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be edited.')
  finally:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  artist_data = ArtistForm(request.form)
  if not artist_data.validate():
      flash('An error occurred. Input data is invalid and a new artist could not be listed')
      return render_template('pages/home.html')
  name = artist_data.name.data
  city = artist_data.city.data
  state = artist_data.state.data
  phone = str(artist_data.phone.data)
  facebook_link  = artist_data.facebook_link.data
  image_link  = artist_data.image_link.data
  website_link  = artist_data.website_link.data
  seeking_venue = artist_data.seeking_venue.data
  seeking_description = artist_data.seeking_description.data
  artist_object = Artists(
    name=name,
    city=city,
    state=state,
    phone=phone,
    website=website_link,
    facebook_link=facebook_link,
    seeking_venue=seeking_venue,
    seeking_description=seeking_description,
    image_link=image_link,
  )
  genres = artist_data.genres.data
  for genre in genres:
    genre_object = Genres.query.filter_by(name=genre).first()
    if genre_object:
      artist_object.genres.append(genre_object)
    else:
      artist_object.genres.append(Genres(name=genre))
  try:
    db.session.add(artist_object)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + name + ' was successfully listed!')
  except:
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  finally:
    return render_template('pages/home.html')





#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = Shows.query.all()
  data = []
  for show in shows:
      data.append(
          {
              "venue_id": show.venue_id,
              "venue_name": show.venue.name,
              "artist_id": show.artist_id,
              "artist_name": show.artist.name,
              "artist_image_link": show.artist.image_link,
              "start_time": str(show.start_time)
          }
      )
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  show_data = ShowForm(request.form)

  artist_id = show_data.artist_id.data
  venue_id = show_data.venue_id.data
  start_time = show_data.start_time.data
  show_object = Shows(
    artist_id=artist_id,
    venue_id= venue_id,
    start_time=start_time
  )
  try:
    db.session.add(show_object)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

