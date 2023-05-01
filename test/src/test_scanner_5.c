#include "test_scanner.h"
#define STATIC_POLY 1
#define STATIC_N_AST 1
#define TOLERANCE 1
#define N_SCANNER_POSITIONS (1 << 14)


int main()
{
    test_scanner_large();
    return 0;
}

void test_scanner_large()
{
    float pos[N_SCANNER_POSITIONS];
    for (int i = 0; i < N_SCANNER_POSITIONS; i++)
    {
        pos[i] = i * i;
    }

    char scanner[SIZEOF_SCANNER(N_SCANNER_POSITIONS)];
    scanner_create(scanner, N_SCANNER_POSITIONS, pos);

    assert(N_SCANNER_POSITIONS == get_num_scanners(scanner));
   
    float* scanner_pos = get_scanner_positions(scanner);
    for (int i = 0; i < N_SCANNER_POSITIONS; i++)
    {
        assert(scanner_pos[i] == pos[i]);
    }
 
}
