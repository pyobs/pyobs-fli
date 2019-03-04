FROM thusser/pytel

# install cfitsio
RUN apt-get update && apt-get install -y libcfitsio-dev

# install pytel-fli
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install

# clean up
RUN rm -rf /src

# set entrypoint
ENTRYPOINT ["bin/pytel", "/pytel.yaml"]