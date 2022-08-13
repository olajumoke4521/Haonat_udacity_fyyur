#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from distutils.log import error
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys

from model import Artist, Show, Venue
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  
  areas = Venue.query.with_entities(Venue.city, Venue.state).distinct(Venue.city, Venue.state).all()
  data = []
  for area in areas:
    venue_query = Venue.query.filter(Venue.state == area.state).filter(Venue.city == area.city).all()

    venue_data = []
    for venue in venue_query:
      venue_data.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
      })

      data.append({
        'city': area.city,
        'state': area.state,
        'venues': venue_data
      })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  count = len(result)
  response = {
        "count": count,
        "data": result
    }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter(Venue.id == venue_id).first()

  past_shows = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
      Show.start_time < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.start_time).all()

  upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
      Show.start_time > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.start_time).all()

  upcoming_shows_data = []

  past_shows_data = []

  for upcoming_show in upcoming_shows:
      upcoming_shows_data.append({
          'artist_id': upcoming_show[1],
          'artist_name': upcoming_show[2],
          'image_link': upcoming_show[3],
          'start_time': str(upcoming_show[4])
      })

  for past_show in past_shows:
      past_shows_data.append({
          'artist_id': past_show[1],
          'artist_name': past_show[2],
          'image_link': past_show[3],
          'start_time': str(past_show[4])
      })

  response = {
      "id": venue.id,
      "name": venue.name,
      "genres": [venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows_data,
      "upcoming_shows": upcoming_shows_data,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=response)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  error = False
  try:
    new_venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        genres=','.join(form.genres.data),
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        website=form.website_link.data,
        seeking_talent= True if 'seeking_talent' in form else False,
        seeking_description=form.seeking_description.data
      )
    db.session.add(new_venue)
    print(request.data)

    db.session.commit()
  # on successful db insert, flash success
    
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else: 
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  count = len(result)
  response = {
        "count": count,
        "data": result
    }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  data = Artist.query.filter(Artist.id == artist_id).first()

  past_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

  upcoming_shows = Show.query.filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()

  past_shows_data = []
  upcoming_shows_data = []

  for upcoming_show in upcoming_shows:
    venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()

    upcoming_shows_data.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(upcoming_show.start_time),
            })

       
    data.upcoming_shows = upcoming_shows_data
    data.upcoming_shows_count = len(upcoming_shows_data)
    
    for past_show in past_shows:
      venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()
      past_shows_data.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(past_show.start_time),
            })

      data.past_shows = past_shows_data
      data.past_shows_count = len(past_shows_data)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).first()
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error=False
  try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.website = request.form['website_link']
      artist.image_link = request.form['image_link']
      artist.facebook_link = request.form['facebook_link']
      artist.seeking_description = request.form['seeking_description']
      db.session.add(artist)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue= Venue.query.filter(Venue.id == venue_id).first()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)

  error = False
  try:
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genre = request.form.getlist('genres')
      venue.facebook_link = request.form['facebook_link']
      venue.image_link=request.form['image_link']
      venue.website=request.form['website_link']
      venue.seeking_talent= True if 'seeking_talent' in request.form else False
      venue.seeking_description=request.form['seeking_description']
      db.session.add(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      else:
          flash('Venue ' + request.form['name'] + ' was successfully updated!')
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  artist_form = ArtistForm(request.form)

  try:
      new_artist = Artist(
          name=artist_form.name.data,
          genres=','.join(artist_form.genres.data),
          city=artist_form.city.data,
          state=artist_form.state.data,
          phone=artist_form.phone.data,
          facebook_link=artist_form.facebook_link.data,
          image_link=artist_form.image_link.data,
          website=artist_form.website_link.data,
          seeking_venue= True if 'seeking_venue' in artist_form else False,
          seeking_description=artist_form.seeking_description.data)

      db.session.add(new_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
# TODO: on unsuccessful db insert, flash an error instead.
# e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()

  data = []
  for show in shows:
      data.append({
          'venue_id': show.venue.id,
          'venue_name': show.venue.name,
          'artist_id': show.artist.id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': str(show.start_time)
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  try:
      show = Show(
          artist_id=request.form['artist_id'],
          venue_id=request.form['venue_id'],
          start_time=request.form['start_time']
      )
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully added!')
  except Exception as e:
      print(e)
      flash('An error occurred. Show could not be added')
      db.session.rollback()
  finally:
      db.session.close()
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
