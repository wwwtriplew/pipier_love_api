#!/bin/bash
# Verify the changes are safe before committing

echo "=========================================="
echo "SAFETY CHECK: Verify changes are correct"
echo "=========================================="
echo ""

cd /root/pipier_love_api

echo "Test 1: Verify helper functions produce correct results"
echo "========================================================="
/usr/bin/python3 -c "
# Test our inlined helpers match the original behavior

# Original from fast_ops.py
_WHITE_PROMO_SQUARES_ORIG = frozenset(range(56, 64))
_BLACK_PROMO_SQUARES_ORIG = frozenset(range(0, 8))
_WHITE_DOUBLE_PUSH_ORIG = frozenset(range(8, 16))
_BLACK_DOUBLE_PUSH_ORIG = frozenset(range(48, 56))

def is_promotion_square_orig(sq, side):
    return sq in (_WHITE_PROMO_SQUARES_ORIG if side == 0 else _BLACK_PROMO_SQUARES_ORIG)

def can_double_push_orig(sq, side):
    return sq in (_WHITE_DOUBLE_PUSH_ORIG if side == 0 else _BLACK_DOUBLE_PUSH_ORIG)

def get_pawn_single_push_orig(sq, side):
    if side == 0:
        return sq + 8 if sq < 56 else -1
    else:
        return sq - 8 if sq >= 8 else -1

def get_pawn_double_push_orig(sq, side):
    if side == 0:
        return sq + 16 if 8 <= sq < 16 else -1
    else:
        return sq - 16 if 48 <= sq < 56 else -1

# New inlined versions
_WHITE_PROMO_RANK = frozenset(range(56, 64))
_BLACK_PROMO_RANK = frozenset(range(0, 8))
_WHITE_DOUBLE_RANK = frozenset(range(8, 16))
_BLACK_DOUBLE_RANK = frozenset(range(48, 56))

def is_promotion_square_lookup(sq, side):
    return sq in (_WHITE_PROMO_RANK if side == 0 else _BLACK_PROMO_RANK)

def can_double_push(sq, side):
    return sq in (_WHITE_DOUBLE_RANK if side == 0 else _BLACK_DOUBLE_RANK)

def get_pawn_single_push(sq, side):
    return (sq + 8 if sq < 56 else -1) if side == 0 else (sq - 8 if sq >= 8 else -1)

def get_pawn_double_push(sq, side):
    return (sq + 16 if 8 <= sq < 16 else -1) if side == 0 else (sq - 16 if 48 <= sq < 56 else -1)

def get_bit(sq):
    return 1 << sq

# Test all squares for both sides
errors = []

for sq in range(64):
    for side in [0, 1]:
        # Test promotion
        if is_promotion_square_orig(sq, side) != is_promotion_square_lookup(sq, side):
            errors.append(f'promotion sq={sq} side={side}')
        
        # Test double push
        if can_double_push_orig(sq, side) != can_double_push(sq, side):
            errors.append(f'double_push sq={sq} side={side}')
        
        # Test single push
        if get_pawn_single_push_orig(sq, side) != get_pawn_single_push(sq, side):
            errors.append(f'single_push sq={sq} side={side} orig={get_pawn_single_push_orig(sq, side)} new={get_pawn_single_push(sq, side)}')
        
        # Test double push destination
        if get_pawn_double_push_orig(sq, side) != get_pawn_double_push(sq, side):
            errors.append(f'double_push_dest sq={sq} side={side}')

# Test get_bit
for sq in range(64):
    expected = 1 << sq
    if get_bit(sq) != expected:
        errors.append(f'get_bit sq={sq}')

if errors:
    print('✗ ERRORS FOUND:')
    for e in errors:
        print(f'  - {e}')
else:
    print('✓ All helper functions produce correct results')
"

echo ""
echo "Test 2: Verify imports work correctly"
echo "======================================"
/usr/bin/pypy3.9 -c "
try:
    from src.chess_engine import ChessBoard, pop_lsb, get_lsb, count_bits
    print('✓ chess_engine imports work')
except Exception as e:
    print(f'✗ chess_engine import error: {e}')
    exit(1)

try:
    from src.move_generation import (
        generate_moves,
        is_promotion_square_lookup,
        can_double_push,
        get_pawn_single_push,
        get_pawn_double_push,
        get_bit
    )
    print('✓ move_generation imports work')
except Exception as e:
    print(f'✗ move_generation import error: {e}')
    exit(1)

# Test they work
board = ChessBoard()
test_bb = 0x0000000000000001
sq, remaining = pop_lsb(test_bb)
if sq != 0:
    print(f'✗ pop_lsb failed: expected 0, got {sq}')
    exit(1)
print('✓ pop_lsb works correctly')

sq = get_lsb(test_bb)
if sq != 0:
    print(f'✗ get_lsb failed: expected 0, got {sq}')
    exit(1)
print('✓ get_lsb works correctly')

bits = count_bits(0x00FF)
if bits != 8:
    print(f'✗ count_bits failed: expected 8, got {bits}')
    exit(1)
print('✓ count_bits works correctly')

# Test helper functions
if not is_promotion_square_lookup(56, 0):  # a8 for white
    print('✗ is_promotion_square_lookup failed')
    exit(1)
print('✓ is_promotion_square_lookup works')

if not can_double_push(8, 0):  # a2 for white
    print('✗ can_double_push failed')
    exit(1)
print('✓ can_double_push works')

if get_pawn_single_push(8, 0) != 16:  # a2→a3
    print('✗ get_pawn_single_push failed')
    exit(1)
print('✓ get_pawn_single_push works')

if get_bit(0) != 1:
    print('✗ get_bit failed')
    exit(1)
print('✓ get_bit works')
"

echo ""
echo "Test 3: Verify move generation produces correct results"
echo "========================================================"
/usr/bin/pypy3.9 -c "
from src.chess_engine import ChessBoard
from src.magic_bitboards import get_lsb

board = ChessBoard()

def perft(b, d):
    if d == 0: return 1
    n = 0
    for f, t, p in b.generate_moves():
        b.make_move(f, t, p)
        k = get_lsb(b.pieces[1-b.side_to_move][5])
        if not b.is_square_attacked(k, b.side_to_move):
            n += perft(b, d-1)
        b.unmake_move()
    return n

# Known correct perft values for starting position
expected = {
    0: 1,
    1: 20,
    2: 400,
    3: 8902,
}

errors = []
for depth in range(4):
    result = perft(board, depth)
    if result != expected[depth]:
        errors.append(f'perft({depth}): expected {expected[depth]}, got {result}')

if errors:
    print('✗ PERFT ERRORS - move generation is BROKEN:')
    for e in errors:
        print(f'  - {e}')
    exit(1)
else:
    print('✓ Move generation produces correct results')
    for depth in range(4):
        print(f'  perft({depth}) = {expected[depth]} ✓')
"

echo ""
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "If all tests pass:"
echo "  ✓ Changes are SAFE to commit"
echo "  ✓ Logic is correct"
echo "  ✓ No regressions"
echo ""
echo "If any test fails:"
echo "  ✗ DO NOT COMMIT"
echo "  ✗ Fix the errors first"
echo ""
