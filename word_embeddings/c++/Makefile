PYTHON_INCLUDE = -I/usr/include/python3.5m

all: swig_wrap embutils_obj shared_obj

shared_obj: embutils_obj swig_obj
	g++ -shared embutils.o embutils_wrap.o -o _embutils.so

embutils_obj: embutils.cc embutils.h
	g++ -Ofast -c embutils.cc -fPIC

swig_obj: swig_wrap
	g++ -O2 -fPIC -c embutils_wrap.cxx $(PYTHON_INCLUDE)

swig_wrap: embutils.i
	swig -c++ -python embutils.i

clean:
	rm embutils.o _embutils.so embutils_wrap.cxx embutils_wrap.o
