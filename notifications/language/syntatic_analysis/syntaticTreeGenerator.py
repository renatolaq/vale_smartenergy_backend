from notifications.language.lexical_analysis.lexeme import LexemeTypes, Lexeme
from notifications.language.parser.lib import ExpressionTypes, operators

## util
# get blocks filtering by indexes and encapsulated array
def get_filtered_array(array, index_start=None, index_end=None):
    if index_start == None:
        index_start = 0
    if index_end == None:
        index_end = len(array)

    result = array[index_start:index_end]

    return result[0] if len(result) == 1 and type(result[0]) != Lexeme else result


class SyntaticTreeGenerator:
    def generate(self, lexemes):
        result = Result()

        # separate blocks with parenthesis as priority blocks
        priority_blocks_generator = PriorityBlocksGenerator()
        priority_blocks = priority_blocks_generator.generate(lexemes)

        # generate syntatic tree
        logical_blocks_generator = LogicalBlocksGenerator()
        syntatic_tree = logical_blocks_generator.generate(priority_blocks)

        # transform tree into dict
        result.syntatic_tree = syntatic_tree
        result.dict_tree = self.get_tree_as_dict(syntatic_tree)

        return result

    def get_tree_as_dict(self, tree):

        if tree.type == ExpressionTypes.LOGICAL_OPERATION:
            return {
                "type": tree.type.value,
                "operator_left": self.get_tree_as_dict(tree.operator_left),
                "operation": tree.operation.value,
                "operator_right": self.get_tree_as_dict(tree.operator_right),
            }

        if tree.type == ExpressionTypes.LOGICAL_COMPARISON:
            return {
                "type": tree.type.value,
                "field": self.get_tree_as_dict(tree.field),
                "operation": operators[tree.operation.value],
                "value": self.get_tree_as_dict(tree.value),
            }

        if tree.type == ExpressionTypes.ARITIMETICAL_OPERATION:
            return {
                "type": tree.type.value,
                "operator_left": self.get_tree_as_dict(tree.operator_left),
                "operation": tree.operation.value,
                "operator_right": self.get_tree_as_dict(tree.operator_right),
            }

        if type(tree) == Lexeme:
            raw_value = (
                tree.value.replace('"', "")
                .replace("$", "")
                .replace("{", "")
                .replace("}", "")
            )

            return {
                "value": raw_value,
                "type": tree.type.value,
            }

        return tree.value


class PriorityBlocksGenerator:
    def generate(self, lexemes):
        result = []

        # aux variable to identify if has found an open parenthesis
        found_open = False
        # count of others open parenthesis to validate the close parenthesis
        count_after_open = 0
        lexemes_inside_parenthesis = []

        for lexeme in lexemes:

            if found_open:
                # it has encountered an open parenthesis
                if lexeme.type == LexemeTypes.OPA:
                    count_after_open += 1
                elif lexeme.type == LexemeTypes.EPA:
                    count_after_open -= 1
                    if count_after_open == 0:
                        if len(lexemes_inside_parenthesis) > 0:
                            result.append(self.generate(lexemes_inside_parenthesis))
                        found_open = False
                        lexemes_inside_parenthesis = []
                        continue

                lexemes_inside_parenthesis.append(lexeme)
            else:
                # no open parenthesis until now
                if lexeme.type == LexemeTypes.OPA:
                    count_after_open += 1
                    # it have found an open parenthesis
                    found_open = True
                    continue

                result.append(lexeme)

        return self.clear(result)

    # this function was used just to test the priority tree
    def get_priorities_as_dict(self, priorities):
        result = []

        if len(priorities) == 1:
            if type(priorities[0]) != Lexeme:
                return self.get_priorities_as_dict(priorities[0])

        for priority in priorities:
            if type(priority) == Lexeme:
                result.append({"type": priority.type.value, "value": priority.value})
            else:
                result.append(self.get_priorities_as_dict(priority))

        return result

    # remove unnecessary parenthesis to prevent generation errors
    def clear(self, priorities):
        result = []

        if type(priorities) == Lexeme:
            return priorities

        if len(priorities) == 1:
            if type(priorities[0]) != Lexeme:
                return self.clear(priorities[0])

        for priority in priorities:
                result.append(self.clear(priority))

        return result


class LogicalBlock:
    def __init__(self):
        self.type = ExpressionTypes.LOGICAL_OPERATION
        self.operation = Lexeme(None)
        self.operator_left = []
        self.operator_right = []


class LogicalBlocksGenerator:
    def __init__(self):
        self.comparison_blocks_generator = ComparisonBlocksGenerator()

    def generate(self, priority_blocks):

        # check each lexeme on priority list for logical operation
        for index, lexeme in enumerate(priority_blocks):
            if type(lexeme) == Lexeme:
                # oh, we found a logical operation
                if lexeme.type == LexemeTypes.LO:
                    # filter priorities on the left of the operation
                    left_priorities = get_filtered_array(priority_blocks, 0, index)
                    # filter priorities on the right of the operation
                    right_priorities = get_filtered_array(
                        priority_blocks, index + 1, len(priority_blocks)
                    )

                    # generates and returns logical block
                    logical_block = LogicalBlock()
                    logical_block.operation = lexeme
                    # the operations will be generated recursively
                    logical_block.operator_left = self.generate(left_priorities)
                    logical_block.operator_right = self.generate(right_priorities)

                    return logical_block

        # if it's not a logical sequence, we need to transform it into a comparison block
        return self.comparison_blocks_generator.generate(
            get_filtered_array(priority_blocks)
        )


class ComparisonBlock:
    def __init__(self, operation, field, value):
        self.type = ExpressionTypes.LOGICAL_COMPARISON
        self.operation = operation
        self.field = field
        self.value = value


class ComparisonBlocksGenerator:
    def __init__(self):
        self.arithmetical_block_generator = ArithmeticalBlockGenerator()

    def generate(self, priority_blocks):
        current_priority_blocks = []

        # the first block will aways contain a field to be compared (the syntatic analysis ensures this for us)
        field = priority_blocks[0]

        # the second lexeme will aways be a comparison operator
        operation = priority_blocks[1]

        # it's value will be an algebrical or value
        # so.. we need to get lasts lexemes and generate another block to get values
        remaining_blocks = []
        last_lexemes = priority_blocks[2 : len(priority_blocks)]

        # in this step we know that all remaining blocks is arithmetical operation or value
        value = self.arithmetical_block_generator.generate(last_lexemes)

        # generate comparison block
        comparison_block = ComparisonBlock(operation, field, value)

        return comparison_block


class ArithmeticalBlock:
    def __init__(self):
        self.type = ExpressionTypes.ARITIMETICAL_OPERATION
        self.operator_left = None
        self.operator_right = None
        self.operation = None


class ArithmeticalBlockGenerator:
    def generate(self, priority_blocks):

        # ensure that the operation is not like "(opr)"
        filtered_blocks = get_filtered_array(priority_blocks)

        # check each lexeme on priority list for logical comparison
        for index, lexeme in enumerate(filtered_blocks):
            if type(lexeme) == Lexeme:
                # oh, we found a logical comparison
                if lexeme.type == LexemeTypes.AR:
                    # filter priorities on the left of the comparison
                    left_priorities = get_filtered_array(filtered_blocks, 0, index)
                    # filter priorities on the right of the comparison
                    right_priorities = get_filtered_array(
                        filtered_blocks, index + 1, len(filtered_blocks)
                    )

                    # generates and returns logical block
                    arithmetical_block = ArithmeticalBlock()
                    arithmetical_block.operation = lexeme
                    # the comparisons will be generated recursively
                    arithmetical_block.operator_left = self.generate(left_priorities)
                    arithmetical_block.operator_right = self.generate(right_priorities)

                    return arithmetical_block

        return filtered_blocks[0]


class Result:
    def __init__(self):
        self.syntatic_tree = None
        self.dict_tree = None
