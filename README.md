# Readme

These modifications are specific to codechef c++ programmers. May add support for other languages in future.
### Build system
see codechef/codechef_c++.sublime-build. This adds a codechef specific build system to your sublime text. to use this build system for C++, use tools->build system->codechef_c++. make sure that:
* You have g++ in your path. I recommend installing dev-c++ and adding C:\Dev-Cpp\bin to your path. You can also use cygwin and keep its g++ in path but I was getting "Access denied" when compiling with cygwin's g++ so I used Dev-C++.
* You have an input file(txt) with the same base name as your cpp file. so if your cpp file is my.cpp then the there should be a my.txt file in the same directory
* The full path to your cpp file does not have any spaces.

After setting the build system, you can just do `Ctrl+Shift+B` and see the program output just below the editing area


***NOTE***: **while compiling the `DEBUG` flag will be on.** So you can surround any dirty printing in `#define DEBUG ... #endif`

### Snippet
see codechef/codechef_c++.sublime-snippet. This adds a new snippet for your cpp files.

#### Usage
1. open a .cpp file. If you are making a new file, first save it with cpp extension.
2. type codechef, you will see a suggestion kind of dropdown, press enter on that
3. navigate with `tab` and `shift+tab` between the provided places. You can still move between after modifying one of them
4. Write additional `#include`s in the first place, if any. if not, move forward with `tab`
5. Second place is for your structs and typedefs. Hopefully by the time you reach here, you have already thought of the data structure you are going to use.
6. Usually codechef has number of test cases as the first line. If it isn't there in the question, Just leave it be. What you can do here is to change the name of this variable.
7. Next you enter the variables which will be scanned once every test case. try entering any of these and you'll understand. 

    
        int a,b,c;
        long long int a,b,c;
        long long int a, b; int c,d;
        long long a,b; int c,d; long long int w;
Use only `int` , `long long` or `long long int`. You see that for a variable name `var`, a statement `s(var)` is added. `s` is a macro which scans numeric inputs efficiently. Won't work on float etc. For other than numeric types, it will add the `s(var)` statement but you will have to change it accordingly(`sf(var)` for float, `ss(var)` for string(char[]), etc. You can look these up in the code.)

8. If you have any other need of global variables, put them here
9. You can change the namespace.
10. If the input has number of test cases first, press `tab` to move forward, otherwise change it however you want
11. change scanning functions appropriately
12. Write your computation for a single loop. This is intented to be your top level logic. You don't need to go up in the code to define auxiliary functions. First write this part and later define other functions in the next step
13. Define additional functions

#### Tips
* To print arbitrary number of variables(debugging) use `debug(a,b,c /*and any more variables comma separated*/)`. You don't even need to remove your `debug` statements. No printing will occur in production. 
* `vector`, `set` or `map` can be printed easily by `cout<<v`. You can even pas a `vector`, `set` or `map` to `debug` as one of its arguments

## How to Install
to install, download the zip, extract it and copy the extracted directory to your packages directory. On windows, packages directory is at `%appdata%\Sublime Text 2\Packages`. Make sure your structure looks like this:

        Packages
        |
        |-SublimeCodechef
          |
          |--codechef_c++.sublime-build
          |--codechef_c++.sublime-snippet



**Any suggestions are welcome!**

**Acknowledgement**: partly taken from [Nikhil Garg's Answer on quora](http://www.quora.com/C++-programming-language/What-are-the-basic-macros-that-are-used-in-programming-contests)