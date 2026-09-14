"""The three states of the redacted-password marker, at the serializer boundary.

Companion to the browser-driven regression test for #5795: this pins the
mapping itself, including the `unknown` state, which needs a node whose
snapshot carried no value data at all — not something a real page can be asked
for on demand.
"""

from browser_use.dom.serializer.serializer import DOMTreeSerializer
from browser_use.dom.views import EnhancedDOMTreeNode, EnhancedSnapshotNode, NodeType

INCLUDE = ['type', 'id', 'value']


def _snapshot(input_value_present: bool | None) -> EnhancedSnapshotNode:
	return EnhancedSnapshotNode(
		is_clickable=None,
		cursor_style=None,
		bounds=None,
		clientRects=None,
		scrollRects=None,
		computed_styles={},
		paint_order=None,
		stacking_contexts=None,
		input_value_present=input_value_present,
	)


def _input(field_type: str, snapshot_node: EnhancedSnapshotNode | None) -> EnhancedDOMTreeNode:
	return EnhancedDOMTreeNode(
		node_id=1,
		backend_node_id=1,
		node_type=NodeType.ELEMENT_NODE,
		node_name='INPUT',
		node_value='',
		attributes={'type': field_type, 'id': 'pw'},
		is_scrollable=None,
		is_visible=True,
		absolute_position=None,
		target_id='test-target',
		frame_id=None,
		session_id=None,
		content_document=None,
		shadow_root_type=None,
		shadow_roots=None,
		parent_node=None,
		children_nodes=None,
		ax_node=None,
		snapshot_node=snapshot_node,
	)


def _attrs(node: EnhancedDOMTreeNode) -> str:
	return DOMTreeSerializer._build_attributes_string(node, INCLUDE, '')


class TestPasswordValueState:
	def test_a_filled_password_is_marked_filled(self):
		assert 'value-state=filled' in _attrs(_input('password', _snapshot(True)))

	def test_an_empty_password_is_marked_empty(self):
		assert 'value-state=empty' in _attrs(_input('password', _snapshot(False)))

	def test_a_password_without_value_data_is_marked_unknown(self):
		"""No snapshot value data for the document, or no snapshot node at all."""
		assert 'value-state=unknown' in _attrs(_input('password', _snapshot(None)))
		assert 'value-state=unknown' in _attrs(_input('password', None))

	def test_the_marker_is_only_for_passwords(self):
		for field_type in ('text', 'email', 'search'):
			assert 'value-state' not in _attrs(_input(field_type, _snapshot(True))), field_type
