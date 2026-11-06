"""What the student has done in the Quantum ML area, for lab checks (no Qt).

The experiments record each preparation and training run here; listeners (the Learn window)
are told, so lab steps tick as soon as their condition is met.
"""
STATE = {'dataset': None, 'features': None, 'classes': None, 'kernel': None, 'variational': None}
_listeners = []


def listen(callback):
    if callback not in _listeners:
        _listeners.append(callback)


def _changed():
    for callback in list(_listeners):
        try:
            callback()
        except RuntimeError:                       # a deleted Qt object: forget it
            _listeners.remove(callback)


def prepared(key, features, classes):
    STATE.update(dataset=key, features=int(features), classes=tuple(classes))
    _changed()


def trained(kind, **result):
    """kind 'kernel' or 'variational'; result: train, test, and the settings used (map, bandwidth, …)."""
    STATE[kind] = dict(result, dataset=STATE.get('dataset') if result.get('dataset') is None else result['dataset'])
    _changed()


def reset():
    for key in STATE:
        STATE[key] = None
    _changed()


def _compare(value, rest):
    op, number = rest.split()[0], float(rest.split()[1])
    return {'>=': value >= number, '<=': value <= number, '=': abs(value - number) < 1e-9,
            '>': value > number, '<': value < number}[op]


def check(rest):
    """(passed?, explanation) for a 'qml …' lab condition:
        qml dataset mnist          the last data prepared (or trained on) is this dataset
        qml features = 4           the prepared data has this many features (also <=, >=)
        qml kernel test >= 0.95    the kernel classifier's last test accuracy (also train)
        qml kernel map zz          …trained with this feature map (angle or zz)
        qml bandwidth <= 0.5       the kernel classifier's last bandwidth
        qml shots >= 100           the kernel was estimated from at least this many shots
        qml variational test >= 0.85   the variational classifier's last test accuracy (also train)
    """
    words = rest.split()
    if not words:
        return False, 'Empty Quantum ML check'
    what = words[0]
    if what == 'dataset':
        last = [STATE.get('dataset')] + [(STATE.get(k) or {}).get('dataset') for k in ('kernel', 'variational')]
        return words[1] in last, f'use the {words[1]} dataset'
    if what == 'features':
        value = STATE.get('features')
        return value is not None and _compare(value, ' '.join(words[1:])), f'prepare {" ".join(words[1:])} features'
    if what in ('kernel', 'variational'):
        result = STATE.get(what)
        if result is None:
            return False, f'train the {what} classifier'
        if words[1] == 'map':
            return result.get('map') == words[2], f'use the {words[2]} feature map'
        return _compare(result.get(words[1], 0.0), ' '.join(words[2:])), f'{what} {words[1]} accuracy {" ".join(words[2:])}'
    if what in ('bandwidth', 'shots'):
        result = STATE.get('kernel')
        if result is None:
            return False, 'train the kernel classifier'
        return _compare(result.get(what, 0), ' '.join(words[1:])), f'{what} {" ".join(words[1:])}'
    raise ValueError(f'Unknown Quantum ML check: {what}')
