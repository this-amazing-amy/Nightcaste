from nightcaste import behaviour


class TestBehaviourManager:

    def test_configure(self):
        instance = behaviour.BehaviourManager(None, None)
        config = {'component_behaviours': [
            {'component_type': 'InputComponent', 'name': 'InputBehaviour'}]}

        assert 'InputComponent' not in instance.behaviors
        instance.configure(config)
        assert 'InputComponent' in instance.behaviors
        assert isinstance(
            instance.behaviors['InputComponent'],
            behaviour.InputBehaviour)
