# yagdspy
Yet another graph dependency system 

This is a python module that implements the graph dependency checks that tools like __Make__ use. 

Here's an example of how to use it:

```python
    import yagdspy as gds

    
    def my_custom_processing_step(lab_study_mapping_file=None, sample_file=None, base=None, config=None):
        pass

    MyCustomProcessing = gds.create_processing_module(my_custom_processing_step, name='MyCustomProcessing', files=
                                          { 'out output_file1':'work_dir/file.csv',
                                            'in input_file1':'work_dir/foo.csv' })

    base = MyOwnServices()  # object to provide services needed by the processing functions, like logging. Not provided by yagdspy
    config = { 'OUTPUT_DIR': '/path/to/my/output/dir' }
    L = [ MyCustomProcessing(base, config) ]

    gds.make_it_go(L, output_graph='/path/to/my/output.png')
```

This will produce an dependancy graph image showing the links that
yagdspy knows about.  Running the graph with `make_it_go()` will
invoking each service in order by dependencies.  It will first check
the source files exist already. After each stp it will check the
outputs were created.  If some of the files already exist, it will
check that the outputs have a timestamp after the inputs. If so, it
assumes that processing step can be skipped.
