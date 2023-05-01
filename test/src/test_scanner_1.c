#include "test_scanner.h"
#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS_STATIC_TEST 5


int main()
{
    test_scanner_constructor();
    return 0;
}

#define N_SCANNER_POSITIONS_CONSTRUCTOR_TEST 100
void test_scanner_constructor()
{
    float pos[N_SCANNER_POSITIONS_CONSTRUCTOR_TEST];
    for (int i = 0; i < N_SCANNER_POSITIONS_CONSTRUCTOR_TEST; i++)
    {
        pos[i] = i * i;
    }

    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS_CONSTRUCTOR_TEST)];
    scanner_create(scanner, N_SCANNER_POSITIONS_CONSTRUCTOR_TEST, pos);

    assert(N_SCANNER_POSITIONS_CONSTRUCTOR_TEST == get_num_scanners(scanner));
   
    float* scanner_pos = get_scanner_positions(scanner);
    for (int i = 0; i < N_SCANNER_POSITIONS_CONSTRUCTOR_TEST; i++)
    {
        assert(scanner_pos[i] == pos[i]);
    }

 
}


