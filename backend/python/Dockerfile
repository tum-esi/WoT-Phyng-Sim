# Start from the official Ubuntu Bionic (18.04 LTS) image
FROM ubuntu:bionic

# Install any extra things that might be need
RUN echo -e "\n\n\n********** Installing OpenFOAM dependencies **********\n\n\n" && \
    apt-get update -y \
	&& apt-get install -y \
		vim \
		ssh \
		sudo \
		wget \
		software-properties-common ;\
		rm -rf /var/lib/apt/lists/*

# Create user foam
RUN useradd --user-group --create-home --shell /bin/bash foam ;\
        echo "foam ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install OpenFOAM 7 (with ParaView)
# including configuring for use
# plus an extra environment variable to make OpenMPI play nice
RUN echo -e "\n\n\n********** Installing OpenFOAM v7 **********\n\n\n" && \
    sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -" ;\
	add-apt-repository http://dl.openfoam.org/ubuntu ;\
	apt-get update ;\
	apt-get install -y openfoam7 gmsh;\
	rm -rf /var/lib/apt/lists/* ;\
	echo "source /opt/openfoam7/etc/bashrc" >> ~foam/.bashrc ;\
	echo "export OMPI_MCA_btl_vader_single_copy_mechanism=none" >> ~foam/.bashrc

# Install python 3.8
RUN echo -e "\n\n\n********** Installing Python v3.8 **********\n\n\n" && \
    add-apt-repository ppa:deadsnakes/ppa &&  \
    apt-get install -y curl build-essential python3.8 python3.8-dev python3-pip && \
    curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3.8 get-pip.py && \
    rm -rf /var/lib/apt/lists/*

# Copy data
WORKDIR /app
RUN chmod 777 /app

# Copy entrypoint
COPY ./entrypoint.sh .
RUN sed -i "s/\r$//g" ./entrypoint.sh
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

# Grant root to foam user, select him
RUN usermod -G root foam
RUN mkdir -p /wop/cases
RUN chown -R foam:foam /wop/cases
RUN chmod -R 0777 /wop/cases

# Copy project
COPY . ./
RUN chmod -R 0777 errors.json

# Change User
USER foam

# Install project dependencies
COPY ./requirements.txt .
RUN echo -e "\n\n\n********** Installing Python project dependencies **********\n\n\n" && \
    pip3.8 install --user -r requirements.txt

RUN python3.8 workaround.py
