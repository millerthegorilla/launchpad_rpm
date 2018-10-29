import PyQt5.QtCore


class PkgTreeNode(tree_model.TreeNode):
    def __init__(self, state, pkgname, pkgdescription, model=None, parent=None, row=None, checked=False):
        super().__init__(model, parent, row)
        self.name = str(pkgname)
        self.state = str(state)
        self.description = str(pkgdescription)

        self._checked = bool(checked)

        self.parent = parent
        self.children = []

        self.setParent(parent)

    def setParent(self, parent):
        if parent is not None:
            self.parent = parent
            self.parent.appendChild(self)
        else:
            self.parent = None

    def parent(self):
        return self.parent

    def appendChild(self, child):
        self.children.append(child)

    def childAtRow(self, row):
        return self.children[row]

    def rowOfChild(self, child):
        for i, item in enumerate(self.children):
            if item == child:
                return i
        return -1

    def removeChild(self, row):
        value = self.children[row]
        self.children.remove(value)

        return True

    def checked(self):
        return self._checked

    def setChecked(self, checked=True):
        self._checked = bool(checked)

    def __len__(self):
        return len(self.children)


class PkgTree(tree_model.TreeModel):
    def __init__(self, parent=None):
        super().__init__()
        self.treeView = parent

        self.columns = 3
        self.headers = ['Installed', 'Pkg Name', 'Description']

        # Create items
        self.rootItem = PkgTreeNode('on', 'root_pkg', 'this is root')
        itemA = PkgTreeNode('on', 'cadence', 'kxstudio audio management', self.rootItem)
        # itemB = myNode('itemB', 'on', 'this is item B', 'fgh', self.root)
        # itemC = myNode('itemC', 'on', 'this is item C', 'cvb', self.root)
        self.insertRow(itemA, self.rootItem)

    def headerData(self, section, orientation, role):
        if orientation == PyQt5.QtCore.Qt.Horizontal and role == PyQt5.QtCore.Qt.DisplayRole:
            return PyQt5.QtCore.QVariant(self.headers[section])
        return PyQt5.QtCore.QVariant()

    def supportedDropActions(self):
        return PyQt5.QtCore.Qt.CopyAction | PyQt5.QtCore.Qt.MoveAction

    def flags(self, index):
        return PyQt5.QtCore.Qt.ItemIsEnabled | PyQt5.QtCore.Qt.ItemIsSelectable | PyQt5.QtCore.Qt.ItemIsUserCheckable

    def insertRow(self, row, parent):
        return self.insertRows(row, 1, parent)

    def insertRows(self, row, count, parent):
        self.beginInsertRows(parent, row, (row.row() + (count - 1)))
        self.endInsertRows()
        return True

    def removeRow(self, row, parentIndex):
        return self.removeRows(row, 1, parentIndex)

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row)
        node = self.nodeFromIndex(parentIndex)
        node.removeChild(row)
        self.endRemoveRows()

        return True

    def data(self, index, role):

        if not index.isValid():
            return None

        node = self.nodeFromIndex(index)

        if role == PyQt5.QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return PyQt5.QtCore.QVariant(node.name)
            if index.column() == 1:
                return PyQt5.QtCore.QVariant(node.state)
            if index.column() == 2:
                return PyQt5.QtCore.QVariant(node.description)
            if index.column() == 3:
                return PyQt5.QtCore.QVariant(node.otro)
        elif role == PyQt5.QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                if node.checked():
                    return PyQt5.QtCore.Qt.Checked
                return PyQt5.QtCore.Qt.Unchecked

        return PyQt5.QtCore.QVariant()

    def setData(self, index, value, role=PyQt5.QtCore.Qt.EditRole):

        if index.isValid():
            if role == PyQt5.QtCore.Qt.CheckStateRole:
                node = index.internalPointer()
                node.setChecked(not node.checked())
                return True
        return False

    def columnCount(self, parent):
        return self.columns

    def rowCount(self, parent):
        node = self.nodeFromIndex(parent)
        if node is None:
            return 0
        return len(node)

    def parent(self, child):
        if not child.isValid():
            return PyQt5.QtCore.QModelIndex()

        node = self.nodeFromIndex(child)

        if node is None:
            return PyQt5.QtCore.QModelIndex()

        parent = node.parent

        if parent is None:
            return PyQt5.QtCore.QModelIndex()

        grandparent = parent.parent
        if grandparent is None:
            return PyQt5.QtCore.QModelIndex()
        row = grandparent.rowOfChild(parent)

        assert row != -1
        return self.createIndex(row, 0, parent)

    def nodeFromIndex(self, index):
        return index.internalPointer() if index.isValid() else self.root

    def flags(self, index):
        flags = PyQt5.QtCore.Qt.ItemIsEnabled | PyQt5.QtCore.Qt.ItemIsSelectable
        if index.column() == 0:
            return flags | PyQt5.QtCore.Qt.ItemIsUserCheckable
        return flags
