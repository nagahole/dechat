#include "test_flatland.h"

int main()
{
    flatland_two_asteroids();
    return 0;
}

#define POLY_SIZE_Y 3
#define POLY_SIZE_X 2
#define N_AST 2
#define TOLERANCE 1
#define N_SCANNER_POSITIONS 5
void flatland_two_asteroids()
{
    // Create cluster object
    char cluster[SIZEOF_ASTEROID_CLUSTER(N_AST)];
    asteroid_cluster_create(cluster, N_AST, TOLERANCE); 

    // Create Polynomial
    char poly_x_a[SIZEOF_POLYNOMIAL(POLY_SIZE_X)];
    char poly_y_a[SIZEOF_POLYNOMIAL(POLY_SIZE_Y)];
    float poly_vals_x_a[POLY_SIZE_X] = {1, 0};
    float poly_vals_y_a[POLY_SIZE_Y] = {2, -100, 1001};

    char poly_x_b[SIZEOF_POLYNOMIAL(POLY_SIZE_X)];
    char poly_y_b[SIZEOF_POLYNOMIAL(POLY_SIZE_Y)];
    float poly_vals_x_b[POLY_SIZE_X] = {100, 0};
    float poly_vals_y_b[POLY_SIZE_Y] = {2, -50, 1001};

    polynomial_create(poly_x_a, POLY_SIZE_X, poly_vals_x_a);
    polynomial_create(poly_y_a, POLY_SIZE_Y, poly_vals_y_a);

    polynomial_create(poly_x_b, POLY_SIZE_X, poly_vals_x_b);
    polynomial_create(poly_y_b, POLY_SIZE_Y, poly_vals_y_b);


    // Add asteroid to cluster
    asteroid_cluster_add_asteroid(cluster, poly_x_a, poly_y_a); 
    asteroid_cluster_add_asteroid(cluster, poly_x_b, poly_y_b); 

    // Create the scanner
    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    float scanner_pos[N_SCANNER_POSITIONS] = {0, 100, 200, 300, 400}; 
    scanner_create(scanner, N_SCANNER_POSITIONS, scanner_pos); 

    assert(0 == asteroid_cluster_clear(cluster));
    
    flatland_protect(cluster, scanner);
    
    assert(0 == asteroid_cluster_impact(cluster)); 
    assert(1 == asteroid_cluster_clear(cluster));

    return;
}
