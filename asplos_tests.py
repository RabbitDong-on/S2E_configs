#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 EPFL.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Symbolic tests for ASPLOS'14."""

__author__ = "stefan.bucur@epfl.ch (Stefan Bucur)"

# TODO: Rename this file more appropriately.


import argparse
import importlib
import os
import sys

from chef import light

# TODO: Devise more meaningful defaults.
# Idea: use a method to transform a concrete input into a wildcard of the same length.

class SimpleTest(light.SymbolicTest):
    def setUp(self):
        pass
    
    def func1(self, input):
        if input<50:
            return 1
        else:
            return 0
    
    def func2(self,input):
        if input<45:
            return 1
        else:
            return 0

    def runTest(self):
        i=self.getInt("value",100,max_value=100,min_value=0)

        res=(self.func1(i)==self.func2(i))
        if res:
            print("same")
        else:
            print("diff")

class HumanevalTest(light.SymbolicTest):
    def setUp(self):
        pass
    def has_close_elements_A(numbers: List[int], threshold: int) -> bool:
        for i in range(len(numbers)):
            for j in range(i+1, len(numbers)):
                if abs(numbers[i] - numbers[j]) < threshold:
                    return True
        return False

    def has_close_elements_B(numbers: List[int], threshold: int) -> bool:
        sorted_numbers = sorted(numbers)
        for i in range(len(sorted_numbers) - 1):
            if sorted_numbers[i + 1] - sorted_numbers[i] < threshold:
                return True
        return False
    def runTest(self):
        threshold=self.getInt("value",0)
        numbers=self.getString("String",'\x00'*10)
        res=(self.has_close_elements_A(numbers,threshold)==self.has_close_elements_B(numbers,threshold))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests")
    parser.add_argument("--interactive", "-i", action="store_true", default=False,
                        help="Do not automatically end concolic session")
    parser.add_argument("test",
                        help="The test class to execute")
    parser.add_argument("exp_dir", nargs="?",
                        help="The experiment directory used for replay")
    args = parser.parse_args()
    
    test_class = globals().get(args.test)
    if not (test_class and
            isinstance(test_class, type) and
            issubclass(test_class, light.SymbolicTest)):
        print >>sys.stderr, "Invalid test name '%s'." % args.test
        sys.exit(1)
    
    if args.exp_dir:
        import json
        import logging
        
        logging.basicConfig(level=logging.INFO, format='** %(message)s')
        
        replayer = light.SymbolicTestReplayer(test_class)
        with open(os.path.join(args.exp_dir, "hl_test_cases.dat"), "r") as f:
            replayer.replayFromTestCases(f)
        with open(os.path.join(args.exp_dir, "coverage.json"), "w") as f:
            json.dump(replayer.getCoverageReport(), f, indent=True)
    else:
        light.runSymbolic(test_class, interactive=args.interactive)