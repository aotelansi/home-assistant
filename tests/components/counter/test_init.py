"""The tests for the counter component."""
# pylint: disable=protected-access
import asyncio
import unittest
import logging

from homeassistant.core import CoreState, State, Context
from homeassistant.setup import setup_component, async_setup_component
from homeassistant.components.counter import (
    DOMAIN, CONF_INITIAL, CONF_RESTORE, CONF_STEP, CONF_NAME, CONF_ICON)
from homeassistant.const import (ATTR_ICON, ATTR_FRIENDLY_NAME)

from tests.common import (get_test_home_assistant, mock_restore_cache)
from tests.components.counter.common import decrement, increment, reset

_LOGGER = logging.getLogger(__name__)


class TestCounter(unittest.TestCase):
    """Test the counter component."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Set up things to be run when tests are started."""
        self.hass = get_test_home_assistant()

    # pylint: disable=invalid-name
    def tearDown(self):
        """Stop everything that was started."""
        self.hass.stop()

    def test_config(self):
        """Test config."""
        invalid_configs = [
            None,
            1,
            {},
            {'name with space': None},
        ]

        for cfg in invalid_configs:
            assert not setup_component(self.hass, DOMAIN, {DOMAIN: cfg})

    def test_config_options(self):
        """Test configuration options."""
        count_start = len(self.hass.states.entity_ids())

        _LOGGER.debug('ENTITIES @ start: %s', self.hass.states.entity_ids())

        config = {
            DOMAIN: {
                'test_1': {},
                'test_2': {
                    CONF_NAME: 'Hello World',
                    CONF_ICON: 'mdi:work',
                    CONF_INITIAL: 10,
                    CONF_RESTORE: False,
                    CONF_STEP: 5,
                }
            }
        }

        assert setup_component(self.hass, 'counter', config)
        self.hass.block_till_done()

        _LOGGER.debug('ENTITIES: %s', self.hass.states.entity_ids())

        assert count_start + 2 == len(self.hass.states.entity_ids())
        self.hass.block_till_done()

        state_1 = self.hass.states.get('counter.test_1')
        state_2 = self.hass.states.get('counter.test_2')

        assert state_1 is not None
        assert state_2 is not None

        assert 0 == int(state_1.state)
        assert ATTR_ICON not in state_1.attributes
        assert ATTR_FRIENDLY_NAME not in state_1.attributes

        assert 10 == int(state_2.state)
        assert 'Hello World' == \
            state_2.attributes.get(ATTR_FRIENDLY_NAME)
        assert 'mdi:work' == state_2.attributes.get(ATTR_ICON)

    def test_methods(self):
        """Test increment, decrement, and reset methods."""
        config = {
            DOMAIN: {
                'test_1': {},
            }
        }

        assert setup_component(self.hass, 'counter', config)

        entity_id = 'counter.test_1'

        state = self.hass.states.get(entity_id)
        assert 0 == int(state.state)

        increment(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 1 == int(state.state)

        increment(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 2 == int(state.state)

        decrement(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 1 == int(state.state)

        reset(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 0 == int(state.state)

    def test_methods_with_config(self):
        """Test increment, decrement, and reset methods with configuration."""
        config = {
            DOMAIN: {
                'test': {
                    CONF_NAME: 'Hello World',
                    CONF_INITIAL: 10,
                    CONF_STEP: 5,
                }
            }
        }

        assert setup_component(self.hass, 'counter', config)

        entity_id = 'counter.test'

        state = self.hass.states.get(entity_id)
        assert 10 == int(state.state)

        increment(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 15 == int(state.state)

        increment(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 20 == int(state.state)

        decrement(self.hass, entity_id)
        self.hass.block_till_done()

        state = self.hass.states.get(entity_id)
        assert 15 == int(state.state)


@asyncio.coroutine
def test_initial_state_overrules_restore_state(hass):
    """Ensure states are restored on startup."""
    mock_restore_cache(hass, (
        State('counter.test1', '11'),
        State('counter.test2', '-22'),
    ))

    hass.state = CoreState.starting

    yield from async_setup_component(hass, DOMAIN, {
        DOMAIN: {
            'test1': {
                CONF_RESTORE: False,
            },
            'test2': {
                CONF_INITIAL: 10,
                CONF_RESTORE: False,
            },
        }})

    state = hass.states.get('counter.test1')
    assert state
    assert int(state.state) == 0

    state = hass.states.get('counter.test2')
    assert state
    assert int(state.state) == 10


@asyncio.coroutine
def test_restore_state_overrules_initial_state(hass):
    """Ensure states are restored on startup."""
    mock_restore_cache(hass, (
        State('counter.test1', '11'),
        State('counter.test2', '-22'),
    ))

    hass.state = CoreState.starting

    yield from async_setup_component(hass, DOMAIN, {
        DOMAIN: {
            'test1': {},
            'test2': {
                CONF_INITIAL: 10,
            },
        }})

    state = hass.states.get('counter.test1')
    assert state
    assert int(state.state) == 11

    state = hass.states.get('counter.test2')
    assert state
    assert int(state.state) == -22


@asyncio.coroutine
def test_no_initial_state_and_no_restore_state(hass):
    """Ensure that entity is create without initial and restore feature."""
    hass.state = CoreState.starting

    yield from async_setup_component(hass, DOMAIN, {
        DOMAIN: {
            'test1': {
                CONF_STEP: 5,
            }
        }})

    state = hass.states.get('counter.test1')
    assert state
    assert int(state.state) == 0


async def test_counter_context(hass, hass_admin_user):
    """Test that counter context works."""
    assert await async_setup_component(hass, 'counter', {
        'counter': {
            'test': {}
        }
    })

    state = hass.states.get('counter.test')
    assert state is not None

    await hass.services.async_call('counter', 'increment', {
        'entity_id': state.entity_id,
    }, True, Context(user_id=hass_admin_user.id))

    state2 = hass.states.get('counter.test')
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == hass_admin_user.id
