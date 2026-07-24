package com.example.demo;

public class Sample {
    private final int seed;

    public Sample(int seed) {
        this.seed = seed;
    }

    public int compute(int a, int b, int c) {
        int total = 0;
        if (a > 0 && b > 0) {
            for (int i = 0; i < a; i++) {
                if (i % 2 == 0) {
                    total += i;
                } else {
                    while (c > 0) {
                        c--;
                        total++;
                    }
                }
            }
        } else if (a < 0 || b < 0) {
            total = -1;
        } else {
            total = c > 0 ? a + b : 0;
        }
        try {
            if (total < -1) {
                throw new IllegalStateException("bad");
            }
        } catch (IllegalStateException ex) {
            return 0;
        }
        return total;
    }

    public void emptyMethod() {
    }
}
