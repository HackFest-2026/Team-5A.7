from eval.slot_metrics import measure


def test_independent_slot_arithmetic_penalizes_missing_and_unrequested_controls():
    expected = {'filters':{'country':['France','Germany']}, 'date_range':{'start':'2011-01-01','end':'2011-12-31'}}
    actual = {'filters':{'country':['France','Spain']}, 'date_range':{'start':'2011-01-01'}}
    result = measure(expected,actual,['filters','date_range'])
    assert (result['tp'],result['fp'],result['fn']) == (2,2,2)
    assert result['precision'] == result['recall'] == result['f1'] == .5


def test_unannotated_default_controls_do_not_inflate_f1_denominator():
    result = measure({'filters':{}},{'filters':{},'grain':'month','top_n':25},['filters'])
    assert result['f1'] == 1 and result['tp'] == result['fp'] == result['fn'] == 0
