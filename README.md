# Readme

These modifications are specific to codechef c++ programmers. May add support for other languages in future.
### Build system
see codechef/codechef_c++.sublime-build. This adds a codechef specific build system to your sublime text. to use this build system for C++, use tools->build system->codechef_c++. make sure that:
* You have g++ in your path. I recommend installing dev-c++ and adding C:\Dev-Cpp\bin to your path. You can also use cygwin and keep its g++ in path but I was getting "Access denied" when compiling with cygwin's g++ so I used Dev-C++.
* You have an input file(txt) with the same base name as your cpp file. so if your cpp file is my.cpp then the there should be a my.txt file in the same directory
* The full path to your cpp file does not have any spaces.

After setting the build system, you can just do `Ctrl+Shift+B` and see the program output just below the editing area


### Snippet
see codechef/codechef_c++.sublime-snippet. This adds a new snippet for your cpp files. To use this
1. create a new .cpp file. 
2. type codechef, you will see a dropdown, press enter on that
3. use `tab` and `shift+tab` to navigate back and forth. 


Any suggestions are welcome!
