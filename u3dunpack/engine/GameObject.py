from .EditorExtension import EditorExtension
from .PPtr import PPtr


class GameObject(EditorExtension):
    """
    public PPtr<Component>[] m_Components;
    public string m_Name;
    public Transform m_Transform;
    public MeshRenderer m_MeshRenderer;
    public MeshFilter m_MeshFilter;
    public SkinnedMeshRenderer m_SkinnedMeshRenderer;
    public Animator m_Animator;
    public Animation m_Animation;
    """

    def __init__(self, reader):
        super().__init__(reader=reader)
        component_size = reader.readInt()
        self.components = []
        for i in range(component_size):
            if self.version[0] < 5 or (self.version[0] == 5 and self.version[1] < 5):
                first = reader.readInt()
            self.components.append(PPtr(reader))
        self.layer = reader.readInt()
        self.name = reader.readAlignedString()
