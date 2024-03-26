def example_function():
    yield 1
    yield 2
    return "Finished"

generator = example_function()
print(generator)

for value in generator:
    print(value)

try:
    final_result = next(generator)
    print(f"Final Result: {final_result}")
except StopIteration as e:
    print(f"Caught StopIteration: {e.value}")
    