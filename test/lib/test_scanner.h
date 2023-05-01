#ifndef TEST_SCANNER_H
#define TEST_SCANNER_H 1

// For use while testing only
#include <math.h>

#include "test.h"

#include "asteroid.h" 
#include "asteroid_cluster.h"
#include "scanner.h"

void test_scanner_constructor();
void test_scan_static();

void test_scanner_range();
void test_scanner_impact();

void test_scanner_cpy();
void test_scanner_large();
void test_scanner_no_statics();
#endif
