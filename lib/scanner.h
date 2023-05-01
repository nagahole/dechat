#ifndef SCANNER_H
#define SCANNER_H 1

#include "asteroid_cluster.h"
#define SIZEOF_SCANNER(n) (1) // TODO
/*
 * scanner_create
 * Creates a collection of scanners
 * :: void* data            :: Location to store the scanner
 * :: const inst n_scanners :: Number of scanners in this object
 * :: float* x_arr          :: The position of each scanner along y = 0
 * Function acts in place
 */
void scanner_create(
        void* data,
        const int n_scanners,
        float* x_arr);

/*
 * scan
 * Performs a scan
 * :: void* scanner_array         :: Scanner object
 * :: void* asteroid_cluster :: Asteroid cluster to scan
 */
float* scan(
        void* scanner_array,
        void* asteroid_cluster);

/*
 * get_scanner_positions
 * Gets the positions of each scanner
 * :: void* scanner_array :: Scanner object
 * Returns a pointer to an array of scanner positions
 */
float* get_scanner_positions(void* scanner_array);

/*
 * get_num_scanners
 * Returns the number of scanners in the array
 * :: void* scanner_array :: Scanner object
 * Returns the number of scanners in this array
 */
int get_num_scanners(void* scanner);
#endif
