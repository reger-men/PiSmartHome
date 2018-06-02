#!/bin/bash

RELEASE_NUM="3.2"
EXIT_FAILURE=1
OCV_PATH=https://github.com/opencv/opencv/archive/3.2.0.zip
PKGS=
DISTRO=
UBUNTU_VERSION=


#install the dependencies in Ubuntu 16.04
install_prerequisites_ubuntu()
{
    # apt-get doesn't accept timeout in seconds as parameter
    #echo
    #echo "Note: if apt-get becomes non-responsive, try aborting the script and run:"
    #echo "      sudo -E $0"
    #echo

    local minus_y="-y"


    CMDS=("apt-get $minus_y update"
	  "apt-get $minus_y install wget"
	  "apt-get $minus_y install unzip"
	  "apt-get $minus_y install --assume-yes build-essential cmake git"
	  "apt-get $minus_y install --assume-yes pkg-config unzip ffmpeg qtbase5-dev python-dev python3-dev python-numpy python3-numpy"
	  "apt-get $minus_y install --assume-yes libopencv-dev libgtk-3-dev libdc1394-22 libdc1394-22-dev libjpeg-dev libpng12-dev libtiff5-dev libjasper-dev"
	  "apt-get $minus_y install --assume-yes libavcodec-dev libavformat-dev libswscale-dev libxine2-dev libgstreamer0.10-dev libgstreamer-plugins-base0.10-dev"
	  "apt-get $minus_y install --assume-yes libv4l-dev libtbb-dev libfaac-dev libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev"
	  "apt-get $minus_y install --assume-yes libvorbis-dev libxvidcore-dev v4l-utils python-vtk"
	  "apt-get $minus_y install --assume-yes liblapacke-dev libopenblas-dev checkinstall"
	  "apt-get $minus_y install --assume-yes libgdal-dev")

    for cmd in "${CMDS[@]}"; do
        echo $cmd
        eval $cmd
        if [[ $? -ne 0 ]]; then
            echo ERROR: failed to run $cmd >&2
            echo Problem \(or disk space\)? >&2
            echo "                sudo -E $0" >&2
            echo 2. Verify that you have enough disk space, and run the script again. >&2
            exit $EXIT_FAIULRE
        fi
    done
}


check_root_access()
{
    if [[ $EUID -ne 0 ]]; then
        echo "ERROR: you must run this script as root." >&2
        echo "Please try again with "sudo -E $0", or as root." >&2
        exit $EXIT_FAILURE
    fi
}

distro_init()
{
    if [[ $DISTRO == "auto" ]]; then
        if [[ -f /etc/lsb-release ]]; then
            DISTRO="ubuntu"
        else
            DISTRO="generic"
        fi
    fi
}

prompt_for_action()
{
    echo "SH Installer for OpenCV on Ubuntu"
    echo
    echo -n "Running on "
    if [[ $DISTRO == "ubuntu" ]]; then
        echo "Ubuntu $UBUNTU_VERSION"
    else
        echo "Generic distribution"
    fi
    echo
    
    echo "The installer will download (unless they already exist):"
    echo


    if [[ $INTERACTIVE -eq 1 ]]; then
        read -p "Do you want to continue? [y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[yY]$ ]]; then
            echo "Aborting."
            exit $EXIT_FAILURE
        fi
    fi
}

checkinstall()
{
    CMDS=("apt-get install checkinstall")

    for cmd in "${CMDS[@]}"; do
        echo $cmd
        eval $cmd
        if [[ $? -ne 0 ]]; then
            echo ERROR: failed to run $cmd >&2
            echo Problem \(or disk space\)? >&2
            echo "                sudo -E $0" >&2
            echo 2. Verify that you have enough disk space, and run the script again. >&2
            exit $EXIT_FAIULRE
        fi
    done
}


build_install_OCV()
{
    #get the source directory
    BUILD_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    BUILD_DIR="$BUILD_DIR/opencv-3.2.0/build"
    
    CMDS=("cd opencv-3.2.0/"
          "mkdir -p build"
	  "cd build/"    
	  "cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D FORCE_VTK=ON -D WITH_TBB=ON -D WITH_V4L=ON -D WITH_QT=ON -D WITH_OPENGL=ON -D WITH_CUBLAS=ON -D CUDA_NVCC_FLAGS=\"-D_FORCE_INLINES\" -D WITH_GDAL=ON -D WITH_XINE=ON -D BUILD_EXAMPLES=ON .."
	  "make -j $(($(nproc) + 1))"
	  "make install"
	  "/bin/bash -c 'echo \"/usr/local/lib\" > /etc/ld.so.conf.d/opencv.conf'"
	  "echo 'export OpenCV_DIR=${BUILD_DIR}' >> ~/.bashrc"
	  "ldconfig"
	  "apt-get update")

    for cmd in "${CMDS[@]}"; do
        echo $cmd
        eval $cmd
        if [[ $? -ne 0 ]]; then
            echo ERROR: failed to run $cmd >&2
            echo Problem \(or disk space\)? >&2
            echo "                sudo -E $0" >&2
            echo 2. Verify that you have enough disk space, and run the script again. >&2
            exit $EXIT_FAIULRE
        fi
    done
}


download_OCV()
{
    wget -nc $OCV_PATH
    unzip 3.2.0.zip
}


install()
{
    install_prerequisites_ubuntu
    download_OCV
    build_install_OCV
    checkinstall
    popd
}


summary()
{
    echo Installation completed successfully.
}

main()
{
    distro_init
    check_root_access
    prompt_for_action
    install
    summary
}

[[ "$0" == "$BASH_SOURCE" ]] && main "$@"




