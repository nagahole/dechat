#ifndef ASTEROID_H
#define ASTEROID_H 1

#include "polynomial.h"
#include "maths.h"

#define SIZEOF_ASTEROID (1) // TODO
/*
 * asteroid_create
 * Creates an asteroid
 * :: void* data :: The location to store the asteroid data
 * :: fx_args    :: The polynomial for the x coordinates
 * :: fy_args    :: The polynomial fo rthe y coordinates 
 * Acts in place.
 */
void asteroid_create(
        void* data,
        const float tolerance,
        void* fx_args,
        void* fy_args);

/*
 * asteroid_update
 * :: void* asteroid ::
 * Updates the position of the asteroid
 */
void asteroid_update(void* asteroid);

/*
 * asteroid_impact
 * Checks if an asteroid has impacted on flatland
 * :: void* asteroid :: The asteroid that may have impacted
 * Returns 1 if an impact has occured, and 0 otherwise
 */
int asteroid_impact(void* asteroid);

/*
 * asteroid_intercept
 * Attempts to intercept an asteroid at location (x, y)
 * :: void* asteroid  :: Asteroid object to intercept
 * :: float x         :: Guess of the x coordinate
 * :: float y         :: Guess of the y coordinate 
 * :: float tolerance :: The maximum permitted error for the guess
 * Returns 1 if the asteroid is intercepted, and 0 otherwise
 */
char asteroid_intercept(
        void* asteroid,
        const float x,
        const float y);

/*
 * asteroid_distance
 * :: void* asteroid ::
 * :: float x        ::
 * :: float y        ::
 * Returns the distance between the asteroid and x, y. 
 */
float asteroid_distance(
        void* asteroid, 
        const float x, 
        const float y);

#endif
