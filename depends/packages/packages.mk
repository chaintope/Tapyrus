packages:=boost libevent zeromq

qt_packages = qrencode zlib

qt_linux_packages:=qt expat dbus libxcb xcb_proto libXau xproto freetype fontconfig libX11 xextproto libXext xtrans

qt_darwin_packages=qt
qt_mingw32_packages=qt

wallet_packages=bdb

upnp_packages=miniupnpc

darwin_native_packages =

ifneq ($(build_os),darwin)
darwin_native_packages += native_cctools
endif
