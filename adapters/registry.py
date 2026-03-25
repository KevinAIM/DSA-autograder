from adapters.m4_sorts import M4SortsAdapter
from adapters.m5_data_structures import M5DataStructuresAdapter
from adapters.m6_dynamic_programming import M6DynamicProgrammingAdapter

REGISTRY = {
    "M4SortsAdapter": M4SortsAdapter,
    "M5DataStructuresAdapter": M5DataStructuresAdapter,
    "M6DynamicProgrammingAdapter": M6DynamicProgrammingAdapter
}