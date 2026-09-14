"""A redacted password field must still say whether it holds a value.

Regression test for #5795: the redaction that keeps password values out of the
LLM view also erased the only sign that a field was filled, so a filled and an
empty password serialized identically and the agent retyped the password every
time it refreshed the DOM.
"""

import pytest
from pytest_httpserver import HTTPServer

from browser_use.browser.events import NavigateToUrlEvent

SECRET = 'correct-horse-battery-staple'

PAGE = f"""<!DOCTYPE html>
<html><head><title>Sign in</title></head>
<body>
	<label for="filled">Password</label>
	<input id="filled" type="password">
	<label for="blank">Confirm</label>
	<input id="blank" type="password">
	<label for="cleared">Old password</label>
	<input id="cleared" type="password">
	<label for="plain">Username</label>
	<input id="plain" type="text">
	<script>
		document.getElementById('filled').value = {SECRET!r};
		document.getElementById('cleared').value = 'typed-then-removed';
		document.getElementById('cleared').value = '';
		document.getElementById('plain').value = 'ada';
	</script>
</body></html>"""


@pytest.fixture(scope='module')
def http_server():
	server = HTTPServer()
	server.start()
	server.expect_request('/signin').respond_with_data(PAGE, content_type='text/html')
	yield server
	server.stop()


async def test_password_state_is_visible_without_the_password(browser_session, http_server):
	event = browser_session.event_bus.dispatch(NavigateToUrlEvent(url=http_server.url_for('/signin')))
	await event
	await event.event_result(raise_if_any=True, raise_if_none=False)

	state = await browser_session.get_browser_state_summary()
	by_id = {node.attributes.get('id'): node for node in state.dom_state.selector_map.values() if node.attributes}

	# The presence bit is recorded, the value is not.
	assert by_id['filled'].snapshot_node is not None
	assert by_id['filled'].snapshot_node.input_value is None, 'password values must not be captured'
	assert by_id['filled'].snapshot_node.input_value_present is True
	assert by_id['blank'].snapshot_node is not None
	assert by_id['blank'].snapshot_node.input_value_present is not True
	# A field typed into and then emptied reads as empty, not as filled.
	assert by_id['cleared'].snapshot_node is not None
	assert by_id['cleared'].snapshot_node.input_value_present is not True

	llm_view = state.dom_state.llm_representation()
	assert SECRET not in llm_view, 'the password must never reach the LLM view'
	assert 'value-state=filled' in llm_view
	assert 'value-state=empty' in llm_view

	# The marker is the only new thing: the filled field is distinguishable from
	# the empty one, and a non-sensitive field is untouched.
	filled_line = next(line for line in llm_view.splitlines() if 'id=filled' in line)
	blank_line = next(line for line in llm_view.splitlines() if 'id=blank' in line)
	cleared_line = next(line for line in llm_view.splitlines() if 'id=cleared' in line)
	assert 'value-state=filled' in filled_line
	assert 'value-state=empty' in blank_line
	assert 'value-state=empty' in cleared_line
	plain_line = next(line for line in llm_view.splitlines() if 'id=plain' in line)
	assert 'value-state' not in plain_line
	assert 'ada' in plain_line
