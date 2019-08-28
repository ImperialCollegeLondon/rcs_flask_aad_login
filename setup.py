import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "rcs_flask_aad_login",
    version = "0.1.0",
    author = "Simon Clifford",
    author_email = "sclifford@imperial.ac.uk",
    description = "A tool to allow Flask applications to use IC's AAD single sign on",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/ImperialCollegeLondon/rcs-flask-aad-login",
    packages=setuptools.find_packages(),
    install_requires  = [
        'flask',
        'flask-saml',
        'flask-login',
    ]
)
