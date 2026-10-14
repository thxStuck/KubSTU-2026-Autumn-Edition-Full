pragma solidity ^0.8.28;

contract BadRandomnessChallenge {
    // FLAG hidden

    mapping(address => bool) public solved;

    event Solved(address indexed player);

    function guess(uint8 answer) external {
        require(answer == random(), "Wrong guess");

        solved[msg.sender] = true;
        emit Solved(msg.sender);
    }

    function random() public view returns (uint8) {
        return uint8(
            uint256(
                keccak256(
                    abi.encodePacked(
                        blockhash(block.number - 1),
                        block.timestamp
                    )
                )
            )
        );
    }

    function getFlag() external view returns (string memory) {
        require(solved[msg.sender], "Solve first");

        // returns flag
    }
}
