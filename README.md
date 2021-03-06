# barbell-io

A project by Dario Aranguiz and Kashev Dalmia. Can we make a better lifting
tracker than fitnotes?

Backend is written with [flask](http://flask.pocoo.org/), and frontend is
written with [bootstrap](http://getbootstrap.com/). Database is
[SQLite](https://www.sqlite.org/).

## Requirements

To run, you need [python3](https://docs.python.org/3/).

- Install dependencies via `pip install -r requirements.txt`.
- Run `./manage.py runsever -d` to run a development server.
    - Run `./manage.py liveserver` to run a live-reloading development server
      (requires a [browser plugin](https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei?hl=en)).

## TODO

- [x] Historic 1RM estimation chart
- [ ] Historic wilks estimation chart
- [ ] Historic volume chart
- [ ] Social: search for friends via Facebook, see their progress
- [ ] Frontend: we can do better than default boostrap styling
- [ ] Deployment: get this bad boy online
- [ ] Templatize warmup input and allow to include/exclude from volume analytics

See [issues](https://github.com/daranguiz/barbell-io/issues) for more up-to-date todo.

### TODO Analytics

- [ ] Historic volume compared to average
- [ ] Volume per day with stacked bar chart for squat/bench/dead-related lifts
- [ ] Historic RPE comparisons (how much of your time are you maxing vs 70% etc)
- [ ] PR table
- [ ] Percentage volume by core lift
- [ ] Other volume comparisons (brainstorm)
