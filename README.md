# Image-to-Video Web Application — ISS Course Project

A Flask coursework application with image uploads, audio selection, video generation, and user/account pages. The implementation uses Pillow, MoviePy, SQLAlchemy, and the existing static/template assets.

## Repository guide

| Path | Purpose |
|---|---|
| [app.py](app.py) | Flask implementation using Flask-SQLAlchemy and local MySQL configuration |
| [app2.py](app2.py) | Alternate Flask implementation with a separately configured SQLAlchemy database engine |
| [requirements.txt](requirements.txt) | Original Python dependency list |
| [static/](static/) | Browser pages, styles, music, images, and included video assets |
| [templates/](templates/) | Server-rendered templates |

Both application variants are retained. Review their configuration and dependencies before selecting an entry point; they are alternatives rather than two services to launch together.

## Local setup

```bash
python -m pip install -r requirements.txt
```

The checked-in application contains historical database configuration and credentials in source. This documentation update does not change that code. A working database connection and compatible media-processing dependencies are needed before starting the selected variant:

```bash
python app.py
# Alternative entry point after reviewing its separate configuration:
# python app2.py
```

Run from the repository root so the existing relative asset paths resolve. These commands describe the entry points in this historical coursework snapshot; a working deployment has not been validated during documentation cleanup. Do not copy historical credentials into another environment.

## Project context

This is the personal public copy of the group coursework. Team attribution and assignment context should be read alongside the original submission; no contributor roles are inferred here.

### Original classroom reference

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/M9yOg1uw)
