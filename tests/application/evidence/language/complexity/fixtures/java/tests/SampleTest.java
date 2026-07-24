package com.example.demo;

import org.junit.jupiter.api.Test;

public class SampleTest {
    @Test
    public void adds() {
        Sample sample = new Sample(1);
        if (sample.compute(1, 2, 0) > 0) {
            return;
        }
    }
}
