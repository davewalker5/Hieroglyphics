# hieroglyphics

The English to Egyptian Hieroglyphics Transliterator is a tool for perorming a simple transliteration of words and phrases in English to their hieroglyphic equivalent. It is implemented using Python.

The hieroglyphics image contains a distribution of the application implementing a Flask-based web UI hosted on the Flask development server, for personal use only.

## Getting Started

### Prerequisities

In order to run this image you'll need docker installed.

* [Windows](https://docs.docker.com/windows/started)
* [OS X](https://docs.docker.com/mac/started/)
* [Linux](https://docs.docker.com/linux/started/)

### Usage

#### Container Parameters

The following "docker run" parameters are recommended when running the hieroglyphics image:

| Parameter | Value | Purpose |
| --- | --- | --- |
| -d | - | Run as a background  process
| -p | 80:5000 | Expose the container's port 5000 as port 80 on the host |
| --rm | - | Remove the container automatically when it stops |

For example:

```shell
docker run -d -p 80:5000 --rm davewalker5/hieroglyphics:latest
```

The port number "80" can be replaced with any available port on the host.

#### Accessing the application the Image

To run the image, enter the following commands:

```shell
docker run -d -p 80:5000 --rm davewalker5/hieroglyphics:latest
```

Once the container is running, browse to the following URL on the host:

http://localhost:80

You should see the transliteration page, allowing you to enter a phrase to be rendered as hieroglyphics.

## Built With

The hieroglyphics image was been built with the following:

| Aspect | Version |
| --- | --- |
| Python | 3.10.0 |
| Docker Desktop | 20.10.11 |

Other dependencies and their versions are listed in the project's [requirements.txt](https://github.com/davewalker5/Hieroglyphics/blob/main/requirements.txt) file

## Find Us

* [English to Hieroglyphics Transliterator on GitHub](https://github.com/davewalker5/Hieroglyphics)

## Versioning

For the versions available, see the [tags on this repository](https://github.com/davewalker5/Hieroglyphics/tags).

## Authors

* **Dave Walker** - *Initial work* - [LinkedIn](https://www.linkedin.com/in/davewalker5/)

See also the list of [contributors](https://github.com/davewalker5/Hieroglyphics/contributors) who 
participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/davewalker5/Hieroglyphics/blob/master/LICENSE) file for details.
