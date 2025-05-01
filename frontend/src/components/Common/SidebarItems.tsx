import { Box, Flex, Text, useColorModeValue } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";

const items = [
  { title: "Calculator", path: "/calculator" },
];

interface SidebarItemsProps {
  onClose?: () => void;
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const textColor = useColorModeValue("ui.main", "ui.light");
  const bgActive = useColorModeValue("#E2E8F0", "#4A5568");

  const listItems = items.map(({ title, path }) => (
    <Flex
      as={Link}
      to={path}
      w="100%"
      p={2}
      key={title}
      activeProps={{
        style: {
          background: bgActive,
          borderRadius: "12px",
          fontWeight: "bold",
        },
      }}
      color={textColor}
      onClick={onClose}
      _hover={{
          background: bgActive,
          borderRadius: "12px",
      }}
      alignItems="center"
      mb={2}
    >
      <Text ml={3}>{title}</Text>
    </Flex>
  ));

  return (
    <>
      <Box>{listItems}</Box>
    </>
  );
};

export default SidebarItems;
