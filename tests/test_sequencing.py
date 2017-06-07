# Copyright 2016 Fred Hutchinson Cancer Research Center
################################################################################
### Tests


import unittest

import os

import yagdspy as gds



class TestSequencing(unittest.TestCase):

    def test_sequencing1(self):
        class MyOwnService:
            def __init__(self, log_file=None):
                if None != log_file:
                    self.log_out = open(log_file, 'w')
                else:
                    self.log_out = None
            def log(self, msg):
                if None != self.log_out:
                    self.log_out.write(msg + '\n')
                    self.log_out.flush()

            
        base = MyOwnService(log_file='working/log.txt')
        def my_custom_processing_step1(output_file=None, input_file=None, base=None, config=None):
            os.system("touch " + output_file)
            base.log("1")

        def my_custom_processing_step2(output_file=None, input_file=None, base=None, config=None):
            os.system("touch " + output_file)
            base.log("2")

        os.system("touch working/foo.csv") # initial source file

        MyCustomProcessing1 = gds.create_processing_module(my_custom_processing_step1, name='MyCustomProcessing1', files=
                                          { 'out output_file':'{OUTPUT_DIR}/file1.csv',
                                            'in input_file':'{OUTPUT_DIR}/foo.csv' })

        MyCustomProcessing2 = gds.create_processing_module(my_custom_processing_step2, name='MyCustomProcessing2', files=
                                          { 'out output_file':'{OUTPUT_DIR}/file2.csv',
                                            'in input_file':'{OUTPUT_DIR}/file1.csv' })
        config = { 'OUTPUT_DIR': os.path.join(os.getcwd(), 'working')}
        L = [ MyCustomProcessing2(base, config), MyCustomProcessing1(base, config) ]
        gds.make_it_go(L, output_graph='working/output.png', dry_run=False)

        lines = open('working/log.txt').readlines()
        print(lines)
        self.assertTrue(2 == len(lines))
        self.assertTrue(lines == sorted(lines))  # simple test to check consistency of ordering

        



            



if "__main__" == __name__:
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequencing)
    unittest.TextTestRunner(verbosity=2).run(suite);
