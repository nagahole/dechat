#ifndef FLATLAND_TEST_H
#define FLATLAND_TEST_H 1

#ifdef DEBUG
    #define DEBUG_PRINT(...) printf(__VA_ARGS__)
#else
    #define DEBUG_PRINT(...) 
#endif

#define FLOAT_CMP(x, y, eps) ((x - y) * (x - y) < eps * eps) 

#include <stddef.h>
#include <stdio.h>
#include <assert.h>


#endif
