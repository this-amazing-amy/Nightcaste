from nightcaste import behaviour


class TestBehaviourManager:

    def test_configure(self):
        instance = behaviour.BehaviourManager(None, None)
        config = {
            'component_behaviours': [
                {
                    'component_type': 'InputComponent',
                    'impl': ['nightcaste.behaviour', 'InputBehaviour']
                }
            ]
        }

        assert 'InputComponent' not in instance.behaviours
        instance.configure(config)
        assert 'InputComponent' in instance.behaviours
        assert isinstance(
            instance.behaviours['InputComponent'],
            behaviour.InputBehaviour)
